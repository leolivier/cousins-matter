"""Signed-link validation: create tenant + admin, auto-login, set password."""

import logging

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import update_session_auth_hash
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic

from core.mixins import LoginNotRequiredMixin
from members.models import Member
from tenants.forms import uniquify_tenant_slug
from tenants.models import Tenant, TenantSettings

from ..models import TenantRequest
from ..tokens import TenantRequestTokenManager

logger = logging.getLogger(__name__)


class TenantValidateView(LoginNotRequiredMixin, generic.View):
  """Creates tenant + settings + admin member from the signed link, then logs in."""

  def get(self, request, encoded, token):
    tenant_request = TenantRequestTokenManager().decrypt_link(encoded, token)
    if tenant_request is None:
      return self._invalid(request)
    if tenant_request.status == TenantRequest.Status.PENDING and tenant_request.is_expired:
      tenant_request.mark_expired()
    if tenant_request.status != TenantRequest.Status.PENDING or tenant_request.is_expired:
      return self._invalid(request)

    try:
      with transaction.atomic():
        # slug computed at validation time: automatic -2 suffix on collision
        slug = uniquify_tenant_slug(tenant_request.tenant_name)
        tenant = Tenant.objects.create(name=tenant_request.tenant_name, slug=slug)
        TenantSettings.objects.create(tenant=tenant)
        username = tenant_request.email.partition("@")[0]
        member = Member.unscoped.create(
          username=username,
          email=tenant_request.email,
          tenant=tenant,
          role=Member.Role.ADMIN,
          is_active=True,
        )
        # password chosen on the welcome screen right after auto-login
        member.set_unusable_password()
        member.save()
        tenant_request.status = TenantRequest.Status.VALIDATED
        tenant_request.validated_at = timezone.now()
        tenant_request.save(update_fields=["status", "validated_at"])
    except Exception:
      logger.exception("Tenant creation failed for request %s", tenant_request.pk)
      messages.error(request, _("Could not create the family site, please contact support."))
      return redirect("saas:signup")

    # we did not authenticate through a backend: name one explicitly (multi-backends setup)
    login(request, member, backend="django.contrib.auth.backends.ModelBackend")
    messages.success(request, _("Your family site is ready! Choose a password to finish."))
    return redirect("saas:welcome")

  def _invalid(self, request):
    messages.error(request, _("This link is invalid or has expired, please submit a new request."))
    return redirect("saas:signup")


class WelcomeView(LoginRequiredMixin, generic.FormView):
  """First screen after validation: choose the admin password."""

  template_name = "saas/welcome.html"
  form_class = SetPasswordForm
  success_url = reverse_lazy("core:Home")

  def dispatch(self, request, *args, **kwargs):
    if request.user.has_usable_password():
      return redirect("core:Home")
    return super().dispatch(request, *args, **kwargs)

  def get_form_kwargs(self):
    kwargs = super().get_form_kwargs()
    kwargs["user"] = self.request.user
    return kwargs

  def form_valid(self, form):
    form.save()
    # keep the session valid after the password hash changed
    update_session_auth_hash(self.request, form.user)
    messages.success(self.request, _("Password set, welcome to your new family site!"))
    return super().form_valid(form)
