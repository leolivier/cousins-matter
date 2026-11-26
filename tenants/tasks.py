"""Asynchronous tenant data export.

``build_tenant_export`` runs in a Django-Q worker (no request): it activates
the export's tenant, writes one XLSX (one sheet per tenant-scoped model) plus
every media file of the tenant into a ZIP, then emails the requester a link.
The ZIP is pruned once ``TENANT_EXPORT_TTL_DAYS`` have passed.
"""

import json
import logging
import os
import posixpath
import re
import shutil
import tempfile
import uuid
import zipfile
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO

from django.apps import apps
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from openpyxl import Workbook

from .models import Tenant, TenantExport
from .rls import set_rls_bypass
from .scoping import tenant_context
from .settings_overrides import tenant_setting

logger = logging.getLogger(__name__)

# Characters Excel forbids in a sheet name.
_INVALID_SHEET_CHARS = re.compile(r"[\\/*?:\[\]]")
# Columns that must never leave the server in a downloadable file.
_EXCLUDED_COLUMNS = {"tenant", "password"}


def build_tenant_export(export_id: int) -> None:
  """Build the export ZIP, then email its link to the requester."""
  # The worker has no request-scoped tenant: read the row with RLS bypass,
  # then activate its tenant for everything else.
  set_rls_bypass(True)
  try:
    export = TenantExport.unscoped.select_related("tenant", "created_by").get(pk=export_id)
  finally:
    set_rls_bypass(False)
  with tenant_context(export.tenant):
    _prune_expired()
    export.status = TenantExport.Status.RUNNING
    export.save(update_fields=["status"])
    try:
      _build_archive(export)
    except Exception as exc:
      logger.exception("Tenant export %s failed", export.pk)
      export.status = TenantExport.Status.FAILED
      export.error = str(exc)[:2000]
      export.save(update_fields=["status", "error"])
      raise
    export.status = TenantExport.Status.READY
    export.expires_at = timezone.now() + timedelta(days=settings.TENANT_EXPORT_TTL_DAYS)
    # "file" is set by _build_archive's FileField.save(save=False): persist its name too
    export.save(update_fields=["status", "expires_at", "file"])
    _send_ready_email(export)


def _build_archive(export: TenantExport) -> None:
  workbook = _build_workbook(export.tenant)
  with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
      archive.writestr("export.xlsx", workbook)
      for name, arcname in _media_files(export.tenant):
        try:
          # stream each file instead of reading a whole photo library into RAM
          with default_storage.open(name, "rb") as media, archive.open(arcname, "w") as dest:
            shutil.copyfileobj(media, dest)
        except FileNotFoundError:
          # a DB row pointing at a deleted file must not fail the whole export
          logger.warning("Export %s: missing media %s", export.pk, name)
    tmp.seek(0)
    export.file.save(f"{export.token}.zip", File(tmp), save=False)


def _build_workbook(tenant: Tenant) -> bytes:
  """One XLSX sheet per tenant-scoped model, headers in the tenant's language."""
  language = tenant_setting("language_code") or settings.LANGUAGE_CODE
  with translation.override(language):
    workbook = Workbook()
    workbook.remove(workbook.active)
    used_names: set[str] = set()
    for model in _tenant_models():
      _add_sheet(workbook, model, tenant, used_names)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _tenant_models():
  """Every model carrying a direct FK to ``Tenant`` (Member and TenantSettings included)."""
  for model in apps.get_models():
    if model is TenantExport:
      continue
    try:
      field = model._meta.get_field("tenant")
    except FieldDoesNotExist:
      continue
    if field.is_relation and field.related_model is Tenant:
      yield model


def _add_sheet(workbook, model, tenant: Tenant, used_names: set[str]) -> None:
  fields = [f for f in model._meta.concrete_fields if f.name not in _EXCLUDED_COLUMNS]
  many = list(model._meta.many_to_many)
  queryset = model._base_manager.filter(tenant=tenant).order_by("pk")
  related = [f.name for f in model._meta.concrete_fields if f.is_relation and f.name != "tenant"]
  if related:
    # FK cells show the related object's str(), readable outside IT
    queryset = queryset.select_related(*related)

  sheet = workbook.create_sheet(_sheet_name(model, used_names))
  sheet.append([str(f.verbose_name) for f in fields] + [str(f.verbose_name) for f in many])
  for obj in queryset.iterator():
    sheet.append([_cell(obj, f) for f in fields] + [", ".join(str(o) for o in getattr(obj, f.name).all()) for f in many])


def _cell(obj, field):
  value = field.value_from_object(obj)
  if field.is_relation:
    related = getattr(obj, field.name)
    return str(related) if related is not None else ""
  if value is None or value == "":
    return ""
  if field.get_internal_type() in ("FileField", "ImageField"):
    return str(value)
  if isinstance(value, datetime):
    return timezone.localtime(value).replace(tzinfo=None) if timezone.is_aware(value) else value
  if isinstance(value, (dict, list)):
    return json.dumps(value, ensure_ascii=False)
  if isinstance(value, Decimal):
    return float(value)
  if isinstance(value, (uuid.UUID, bytes)):
    return str(value)
  return value


def _sheet_name(model, used_names: set[str]) -> str:
  base = (_INVALID_SHEET_CHARS.sub(" ", str(model._meta.verbose_name_plural)).strip() or model._meta.label)[:31]
  name, index = base, 2
  while name in used_names:
    suffix = f" ({index})"
    name = base[: 31 - len(suffix)] + suffix
    index += 1
  used_names.add(name)
  return name


def _media_files(tenant: Tenant):
  """Yield ``(storage name, archive name)`` for the tenant's media files.

  In multi-tenant mode media live under ``<slug>/``; the export's own
  ``exports/`` folder is skipped so old ZIPs never embed themselves. The
  tenant's public logo (``public/logos/<slug>.*``) is included too.
  """
  prefix = tenant.slug if settings.MULTI_TENANT_ENABLED else ""
  for name in _walk(default_storage, prefix, skip={"exports"} if prefix else set()):
    arcname = name[len(prefix) + 1 :] if prefix and name.startswith(prefix + "/") else name
    yield name, f"media/{arcname}"
  for name in _walk(default_storage, "public/logos"):
    # exact stem match: tenant "smith" must not pick up "smith-cousins.png"
    if os.path.splitext(os.path.basename(name))[0] == tenant.slug:
      yield name, f"media/{name}"


def _walk(storage, prefix: str, skip: set[str] | None = None):
  skip = skip or set()
  try:
    dirs, files = storage.listdir(prefix)
  except (FileNotFoundError, NotImplementedError):
    return
  for filename in files:
    yield posixpath.join(prefix, filename) if prefix else filename
  for dirname in dirs:
    if dirname in skip:
      continue
    yield from _walk(storage, posixpath.join(prefix, dirname) if prefix else dirname)


def _prune_expired() -> None:
  """Delete the current tenant's expired exports (rows + files).

  Called whenever that tenant builds a new export; under RLS the query only
  sees the session tenant anyway. No scheduled job on purpose: the only cost
  of a late prune is a ZIP left on disk until the family exports again.
  """
  for export in TenantExport.unscoped.filter(expires_at__lt=timezone.now()):
    try:
      if export.file:
        export.file.delete(save=False)
    except Exception as exc:  # storage hiccup must not block the new export
      logger.warning("Could not delete expired export %s: %s", export.pk, exc)
    export.delete()


def _send_ready_email(export: TenantExport) -> None:
  recipient = getattr(export.created_by, "email", "")
  if not recipient:
    logger.warning("Export %s is ready but its requester has no email", export.pk)
    return
  language = tenant_setting("language_code") or settings.LANGUAGE_CODE
  with translation.override(language):
    url = _site_url() + reverse("tenants:export_download", args=[export.token])
    expires = timezone.localtime(export.expires_at).date()
    subject = _("Your family data export is ready")
    body = _("Your family data export is ready.\n\nDownload it here: %(url)s\n\nThis link expires on %(date)s.") % {
      "url": url,
      "date": expires.isoformat(),
    }
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient])


def _site_url() -> str:
  domain = settings.SITE_DOMAIN or "localhost"
  port = getattr(settings, "SITE_PORT", 0)
  if isinstance(port, int):
    port = f":{port}" if port and port not in (80, 443) else ""
  scheme = "http" if settings.DEBUG else "https"
  return f"{scheme}://{domain}{port}"
