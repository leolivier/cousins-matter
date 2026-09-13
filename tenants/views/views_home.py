"""Tenant-scoped anonymous home: the pre-tenancy unauthenticated page."""

from django.contrib.auth.views import LoginView
from django.http import Http404
from django.views import generic

from core.mixins import LoginNotRequiredMixin

from ..scoping import tenant_context
from ..services import resolve_join_tenant

# Same view class as members:login, so the family home behaves exactly like
# the global one (login form, language, password reset) — only branding differs.
login_view = LoginView.as_view(template_name="members/login/login.html")


class TenantHomeView(LoginNotRequiredMixin, generic.View):
  def get(self, request, slug):
    return self._scoped(request, slug)

  def post(self, request, slug):
    return self._scoped(request, slug)

  def _scoped(self, request, slug):
    tenant = resolve_join_tenant(slug)
    if tenant is None:
      raise Http404
    request.tenant = tenant
    with tenant_context(tenant):
      return login_view(request)
