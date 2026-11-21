from django import template

from ..onboarding import onboarding_state

register = template.Library()


@register.inclusion_tag("saas/_onboarding.html")
def saas_onboarding(user):
  """Render the onboarding checklist (empty output when nothing to show)."""
  return {"state": onboarding_state(user)}
