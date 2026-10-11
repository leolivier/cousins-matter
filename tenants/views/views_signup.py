"""Self-service "create a family" signup.

A brand-new user (no invitation) creates a new Tenant and becomes its admin
(``role="admin"``). Mirrors the invited-registration flow: the member is saved
inactive and receives a verification email (``send_verification_email`` under
``tenant_context``), exactly like ``RegistrationCheckingView.post``.
"""

import logging

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import generic

from core.mixins import LoginNotRequiredMixin
from members.forms import MemberRegistrationForm
from members.models import Member
from verify_email.email_handler import send_verification_email

from ..forms import TenantCreationForm
from ..models import Tenant, TenantSettings
from ..scoping import tenant_context
from . import multi_tenant_required

logger = logging.getLogger(__name__)

# Simple cache-based signup throttle: max SIGNUP_THROTTLE_LIMIT submissions per
# IP per window, so an attacker cannot create hundreds of tenants in a loop.
SIGNUP_THROTTLE_LIMIT = 5
SIGNUP_THROTTLE_SECONDS = 3600


def _throttled(request) -> bool:
  from django.core.cache import cache

  key = f"tenant-signup:{request.META.get('REMOTE_ADDR', 'unknown')}"
  count = cache.get_or_set(key, 0, SIGNUP_THROTTLE_SECONDS)
  if count >= SIGNUP_THROTTLE_LIMIT:
    return True
  try:
    cache.incr(key)
  except ValueError:
    cache.set(key, 1, SIGNUP_THROTTLE_SECONDS)
  return False


class FamilySignupView(LoginNotRequiredMixin, generic.View):
  """Anonymous signup that creates a new family and its first admin."""

  template_name = "tenants/family_signup.html"
  title = _("Create a new family")

  def get(self, request):
    multi_tenant_required()
    return render(
      request,
      self.template_name,
      {"tenant_form": TenantCreationForm(), "form": MemberRegistrationForm(), "title": self.title},
    )

  def post(self, request):
    multi_tenant_required()
    if _throttled(request):
      messages.error(request, _("Too many signup attempts, please try again later."))
      return redirect("members:login")

    tenant_form = TenantCreationForm(request.POST)
    form = MemberRegistrationForm(request.POST, request.FILES)
    if not tenant_form.is_valid() or not form.is_valid():
      return self._render(request, tenant_form, form)

    email = form.cleaned_data["email"]
    if Member.unscoped.filter(email=email).exists():
      # email login is global: a duplicate email can never join a new family
      form.add_error("email", _("A member with this email address already exists."))
      return self._render(request, tenant_form, form)

    with transaction.atomic():
      tenant = Tenant.objects.create(name=tenant_form.cleaned_data["name"], slug=tenant_form.cleaned_data["slug"])
      TenantSettings.objects.create(tenant=tenant)
      # the creator administers the family they just created
      form.instance.tenant = tenant
      form.instance.role = Member.Role.ADMIN
      # send_verification_email() saves the (inactive) member and emails the
      # activation link; the tenant context makes it land on the new tenant.
      with tenant_context(tenant):
        send_verification_email(request, form)

    messages.success(
      request,
      _(
        "Your family has been created! You will now receive an email to verify your "
        "email address. Click in the link inside the mail to finish the registration."
      ),
    )
    return redirect("members:login")

  def _render(self, request, tenant_form, form):
    return render(
      request,
      self.template_name,
      {"tenant_form": tenant_form, "form": form, "title": self.title},
    )
