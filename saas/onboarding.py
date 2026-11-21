"""Computed onboarding checklist state for a freshly created tenant admin."""

from django.conf import settings

from members.models import Member
from tenants.models import TenantSettings


def onboarding_state(user) -> dict | None:
  """Return the checklist state for a tenant admin, ``None`` when nothing to show.

  Rendered on every page through core/base.html, so keep it silent and cheap
  for anyone but a SaaS tenant admin who hasn't dismissed the checklist yet.
  """
  if not settings.SAAS_LANDING_ENABLED:
    return None
  if not user.is_authenticated or not user.is_tenant_admin:
    return None
  overrides = TenantSettings._base_manager.filter(tenant=user.tenant).values_list("overrides", flat=True).first() or {}
  if overrides.get("saas_onboarding_done"):
    return None
  return {
    "password_set": user.has_usable_password(),
    "profile_done": bool(user.first_name and user.last_name),
    # ponytail: "invited" derives from the tenant having other members instead
    # of an invite-time flag in overrides; switch to a flag only if pending
    # (sent-but-unregistered) invitations must tick the box too.
    "invited": Member.unscoped.filter(tenant=user.tenant).exclude(pk=user.pk).exists(),
  }
