"""Public tenant request flow: Turnstile + email + family name → signed link."""

import logging

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import generic

from core.mixins import LoginNotRequiredMixin
from members.models import Member

from ..forms import SignupRequestForm
from ..services import create_tenant_request, send_tenant_request_email
from ..tokens import TenantRequestTokenManager
from ..turnstile import verify_turnstile

logger = logging.getLogger(__name__)

# Same throttle policy as the tenants family signup: 5 submissions/hour/IP.
SIGNUP_THROTTLE_LIMIT = 5
SIGNUP_THROTTLE_SECONDS = 3600


def _throttled(request) -> bool:
  key = f"saas-signup:{request.META.get('REMOTE_ADDR', 'unknown')}"
  count = cache.get_or_set(key, 0, SIGNUP_THROTTLE_SECONDS) or 0
  if count >= SIGNUP_THROTTLE_LIMIT:
    return True
  try:
    cache.incr(key)
  except ValueError:
    cache.set(key, 1, SIGNUP_THROTTLE_SECONDS)
  return False


class SignupRequestView(LoginNotRequiredMixin, generic.View):
  """Anonymous request for a new family site (captcha + email verification)."""

  template_name = "saas/signup_form.html"

  def get(self, request):
    return self._render(request, SignupRequestForm())

  def post(self, request):
    if not verify_turnstile(request):
      messages.error(request, _("Captcha verification failed, please try again."))
      return redirect("saas:signup")
    if _throttled(request):
      messages.error(request, _("Too many requests, please try again later."))
      return redirect("saas:signup")

    form = SignupRequestForm(request.POST)
    if not form.is_valid():
      return self._render(request, form)

    email = form.cleaned_data["email"]
    if Member.unscoped.filter(email=email).exists():
      # email login is global: an existing member can never re-claim it here
      form.add_error("email", _("A member with this email address already exists."))
      return self._render(request, form)

    tenant_request = create_tenant_request(
      email=email,
      tenant_name=form.cleaned_data["tenant_name"],
      ip=request.META.get("REMOTE_ADDR"),
    )
    # the link needs the request (absolute URI); the service stays request-free
    link = TenantRequestTokenManager().generate_link(request, tenant_request)
    send_tenant_request_email(tenant_request, link)
    return redirect("saas:signup_sent")

  def _render(self, request, form):
    return render(request, self.template_name, {"form": form})


class SignupSentView(LoginNotRequiredMixin, generic.TemplateView):
  """ "Check your mailbox" screen shown after a request is submitted."""

  template_name = "saas/signup_sent.html"

  def get_context_data(self, **kwargs):
    return super().get_context_data(max_age_hours=settings.SAAS_TENANT_REQUEST_MAX_AGE // 3600, **kwargs)
