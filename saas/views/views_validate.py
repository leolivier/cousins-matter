"""Signed-link validation: confirm page, then tenant + admin creation."""

import logging

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

from core.mixins import LoginNotRequiredMixin

from ..services import create_tenant_from_request, resolve_tenant_request

logger = logging.getLogger(__name__)


class TenantValidateView(LoginNotRequiredMixin, generic.View):
  """Signed email link: GET shows the confirmation, POST creates the site."""

  template_name = "saas/validate_confirm.html"

  def get(self, request, encoded, token):
    tenant_request = resolve_tenant_request(encoded, token)
    if tenant_request is None:
      return self._invalid(request)
    # a GET must not create anything: show the confirmation, POST decides
    return render(
      request,
      self.template_name,
      {
        "tenant_name": tenant_request.tenant_name,
        "email": tenant_request.email,
        "encoded": encoded,
        "token": token,
      },
    )

  def post(self, request, encoded, token):
    tenant_request = resolve_tenant_request(encoded, token)
    if tenant_request is None:
      return self._invalid(request)
    try:
      member = create_tenant_from_request(tenant_request)
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
