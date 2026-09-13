"""Tenant lifecycle services (shared by the management UI and the command)."""

import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from .models import Tenant

logger = logging.getLogger(__name__)


def delete_tenant(tenant: Tenant) -> int:
  """Hard-delete ``tenant`` and all its data; returns the member count removed.

  Refuses the system tenant (never deletable) and any still-active tenant —
  deactivation must happen first so the action stays deliberate.
  ``Member.tenant`` is ``on_delete=PROTECT``, so members are removed explicitly
  before the tenant; tenant-scoped rows (galleries, photos) cascade.
  """
  from members.models import Member

  if tenant.is_system:
    raise PermissionDenied(_("The system tenant cannot be deleted."))
  if tenant.is_active:
    raise PermissionDenied(_("This family is still active. Deactivate it before deleting it."))

  member_count = Member.unscoped.filter(tenant=tenant).count()
  Member.unscoped.filter(tenant=tenant).delete()
  name, slug = tenant.name, tenant.slug
  tenant.delete()  # cascades tenant-scoped rows (galleries, photos)
  logger.info(f"Deleted tenant {name!r} ({slug!r}) and {member_count} member(s).")
  return member_count


def resolve_join_tenant(slug: str | None) -> Tenant | None:
  """Tenant targeted by the public join flow (family home, join request).

  With multi-tenancy on, ``slug`` selects the tenant. Without multi-tenancy
  only the default tenant exists: ``None`` (the legacy alias) and the default
  slug resolve to it, any other slug is refused. Returns ``None`` when no
  active tenant matches — callers raise 404.
  """
  default = Tenant.get_default()
  if slug is None:
    return default
  tenant = Tenant.objects.filter(slug=slug).first()
  if tenant is None or not tenant.is_active:
    return None
  if not settings.MULTI_TENANT_ENABLED and tenant.pk != default.pk:
    return None
  return tenant
