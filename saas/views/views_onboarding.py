"""Onboarding checklist dismiss (state itself lives in saas/onboarding.py)."""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from tenants.models import TenantSettings


@require_POST
def dismiss_onboarding(request):
  if not (request.user.is_authenticated and request.user.tenant):
    raise Http404()
  row, _created = TenantSettings.objects.get_or_create(tenant=request.user.tenant)
  row.overrides = {**(row.overrides or {}), "saas_onboarding_done": True}
  row.save(update_fields=["overrides"])
  messages.success(request, _("Checklist dismissed. You can restart it anytime from the docs."))
  return redirect("core:Home")
