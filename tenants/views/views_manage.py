"""Tenant management UI (platform superusers only).

List / create / deactivate / hard-delete families. Mounted under /tenants/
only when MULTI_TENANT_ENABLED is on; every view also checks the flag and
``is_superuser`` (tenant admins are intentionally NOT allowed to manage the
tenant lifecycle — they administer their own family's members and settings).
"""

import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import generic

from members.models import Member

from ..forms import TenantCreationForm
from ..models import Tenant, TenantSettings
from ..services import delete_tenant as delete_tenant_service
from . import multi_tenant_required

logger = logging.getLogger(__name__)


class OnlySuperuserMixin:
  """Allow only platform (cross-tenant) superusers."""

  def dispatch(self, request, *args, **kwargs):
    multi_tenant_required()
    if not request.user.is_authenticated:
      # consistent with the rest of the site: send anonymous users to login
      from django.contrib.auth.views import redirect_to_login

      return redirect_to_login(request.get_full_path())
    if not request.user.is_superuser:
      raise PermissionDenied(_("Only platform administrators can manage families."))
    return super().dispatch(request, *args, **kwargs)


class TenantListView(OnlySuperuserMixin, generic.View):
  template_name = "tenants/tenant_list.html"

  def get(self, request):
    tenants = Tenant.objects.annotate(num_members=Count("members", distinct=True)).order_by("name")
    return render(request, self.template_name, {"tenants": tenants, "title": _("Families")})


class TenantCreateView(OnlySuperuserMixin, generic.View):
  """Create a family; optionally invite its first admin right away."""

  template_name = "tenants/tenant_form.html"

  def get(self, request):
    return render(request, self.template_name, {"form": TenantCreationForm(), "title": _("Create a family")})

  def post(self, request):
    form = TenantCreationForm(request.POST)
    if not form.is_valid():
      return render(request, self.template_name, {"form": form, "title": _("Create a family")})

    tenant = Tenant.objects.create(name=form.cleaned_data["name"], slug=form.cleaned_data["slug"])
    TenantSettings.objects.create(tenant=tenant)
    messages.success(request, _("Family %(name)s created.") % {"name": tenant.name})

    admin_email = request.POST.get("admin_email", "").strip()
    if admin_email:
      if Member.unscoped.filter(email=admin_email).exists():
        messages.error(request, _("A member with this email already exists; invitation not sent."))
      else:
        self._send_admin_invitation(request, tenant, admin_email)
    return redirect("tenants:list")

  @staticmethod
  def _send_admin_invitation(request, tenant, email):
    """Invite ``email`` as the first admin of ``tenant`` (tenant-bound link)."""
    from django.conf import settings as dj_settings
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags

    from members.registration_link_manager import RegistrationLinkManager

    invitation_url = RegistrationLinkManager().generate_link(request, email, tenant_id=tenant.pk)
    msg = render_to_string(
      "tenants/email/tenant_admin_invitation.html",
      {"link": invitation_url, "tenant": tenant, "site_name": dj_settings.SITE_NAME},
      request=request,
    )
    send_mail(
      _("You are invited to administer the family %(name)s") % {"name": tenant.name},
      strip_tags(msg),
      from_email=dj_settings.DEFAULT_FROM_EMAIL,
      recipient_list=[email],
      html_message=msg,
    )
    messages.success(request, _("Invitation sent to %(email)s.") % {"email": email})


class TenantToggleActiveView(OnlySuperuserMixin, generic.View):
  """(De)activate a family. Deactivated families' members are logged out and
  cannot sign in (enforced by TenantMiddleware)."""

  def post(self, request, slug):
    tenant = get_object_or_404(Tenant.objects, slug=slug)
    if tenant.is_system:
      messages.error(request, _("The system family cannot be deactivated."))
      return redirect("tenants:list")
    tenant.is_active = not tenant.is_active
    tenant.save()
    if tenant.is_active:
      messages.success(request, _("Family %(name)s reactivated.") % {"name": tenant.name})
    else:
      messages.warning(request, _("Family %(name)s deactivated.") % {"name": tenant.name})
    return redirect("tenants:list")


class TenantDeleteView(OnlySuperuserMixin, generic.View):
  """Hard-delete a family. Refuses active and system families; requires typing
  the slug as confirmation (same rule as the management command)."""

  template_name = "tenants/tenant_confirm_delete.html"

  def get(self, request, slug):
    tenant = get_object_or_404(Tenant.objects, slug=slug)
    return render(request, self.template_name, {"tenant": tenant})

  def post(self, request, slug):
    tenant = get_object_or_404(Tenant.objects, slug=slug)
    if request.POST.get("confirmation", "").strip() != slug:
      messages.error(request, _("Confirmation did not match the family identifier. Aborting."))
      return render(request, self.template_name, {"tenant": tenant})
    name = tenant.name
    try:
      delete_tenant_service(tenant)
    except PermissionDenied as e:
      messages.error(request, str(e))
      return redirect("tenants:list")
    messages.success(request, _("Family %(name)s permanently deleted.") % {"name": name})
    return redirect("tenants:list")
