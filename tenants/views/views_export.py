"""Tenant data export: request the ZIP (admins) and download it (all members).

Both views also call :func:`multi_tenant_required`, and the download link's
unguessable token is only half the protection: a logged-in member of the
export's tenant is required too, so a forwarded email is not enough.
"""

import logging

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django_q.tasks import async_task

from tenants.authz import is_tenant_admin
from tenants.models import Tenant, TenantExport

from . import multi_tenant_required

logger = logging.getLogger(__name__)


def _login_required(request):
  return redirect_to_login(request.get_full_path())


def _target_tenant(request) -> Tenant:
  """The tenant to export: the caller's, or ``?tenant=<slug>`` for a superuser."""
  if request.user.is_superuser:
    slug = request.POST.get("tenant") or request.GET.get("tenant")
    if slug:
      return get_object_or_404(Tenant.objects, slug=slug)
  return request.user.tenant


class TenantExportCreateView(generic.View):
  """Queue an export of the tenant's data (tenant admins only)."""

  def dispatch(self, request, *args, **kwargs):
    multi_tenant_required()
    if not request.user.is_authenticated:
      return _login_required(request)
    if not is_tenant_admin(request.user):
      raise PermissionDenied(_("Only family administrators can export family data."))
    return super().dispatch(request, *args, **kwargs)

  def post(self, request):
    tenant = _target_tenant(request)
    export = TenantExport.unscoped.create(tenant=tenant, created_by=request.user)
    # Q_CLUSTER's global timeout is 60s; a media-heavy family needs longer.
    async_task("tenants.tasks.build_tenant_export", export.pk, timeout=1800)
    messages.success(
      request,
      _("Export requested. You will receive an email with a download link once it is ready."),
    )
    url = reverse("tenants:settings")
    if request.user.is_superuser and tenant.pk != request.user.tenant_id:
      url += f"?tenant={tenant.slug}"
    return redirect(url)


class TenantExportDownloadView(generic.View):
  """Serve a ready export ZIP to any logged-in member of its tenant."""

  def dispatch(self, request, *args, **kwargs):
    multi_tenant_required()
    if not request.user.is_authenticated:
      return _login_required(request)
    return super().dispatch(request, *args, **kwargs)

  def get(self, request, token):
    export = get_object_or_404(TenantExport.unscoped, token=token)
    if not request.user.is_superuser and request.user.tenant_id != export.tenant_id:
      # 404, not 403: do not reveal that another family's export exists
      raise Http404(_("Export not found."))
    if export.expires_at and export.expires_at <= timezone.now():
      try:
        export.file.delete(save=False)
      except Exception as exc:  # storage hiccup must not keep the row alive
        logger.warning("Could not delete expired export %s: %s", export.pk, exc)
      export.delete()
      raise Http404(_("This export has expired."))
    if export.status != TenantExport.Status.READY or not export.file:
      raise Http404(_("This export is not ready yet."))
    if not export.file.storage.exists(export.file.name):
      raise Http404(_("This export is no longer available."))
    filename = f"export-{export.tenant.slug}-{export.created_at:%Y-%m-%d}.zip"
    return FileResponse(export.file.open("rb"), as_attachment=True, filename=filename, content_type="application/zip")
