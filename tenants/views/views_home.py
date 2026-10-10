"""Tenant-scoped anonymous home: the pre-tenancy unauthenticated page."""

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.views import generic

from core.mixins import LoginNotRequiredMixin
from core.views.views_general import HomeView

from ..scoping import tenant_context
from ..services import resolve_join_tenant


class TenantHomeView(LoginNotRequiredMixin, generic.View):
  def get(self, request, slug):
    tenant = resolve_join_tenant(slug)
    if tenant is None:
      raise Http404
    if request.user.is_authenticated:
      # same contract as the former LoginView: authenticated users have no
      # business on a family home — send them to the site home instead
      return redirect(settings.LOGIN_REDIRECT_URL)
    request.tenant = tenant
    with tenant_context(tenant):
      # the unauthenticated page: flatpage + navbar with Sign in link,
      # rendered with the family's branding and join-request link
      return HomeView.as_view()(request)
