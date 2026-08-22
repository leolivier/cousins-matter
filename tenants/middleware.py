"""Tenant-resolution middleware (auth-based identification)."""

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from .rls import reset_rls, set_rls_bypass, set_rls_tenant
from .scoping import get_current_tenant, set_current_tenant


class TenantMiddleware:
  """Resolve the request's tenant and activate it for the current thread.

  Identification is auth-based: the tenant is the logged-in member's tenant.
  Platform superusers (``is_superuser``) are left unscoped so they can see
  every tenant; anonymous requests are unscoped too — allauth must be able to
  resolve a user by email before the tenant is known.

  ``request.tenant`` is set for use by views/templates (None when unscoped).

  NOTE: PostgreSQL row-level security (``SET app.current_tenant_id``) is
  intentionally NOT applied here yet. RLS is enabled *inert* in migrations
  (the app connects as the table owner, which bypasses RLS), so the session
  variable has no effect today and would only risk leaking connection state
  across pooled connections. It will be wired in together with a dedicated
  non-owner DB role (the RLS hardening step).
  """

  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    user = getattr(request, "user", None)
    request.tenant = None
    # Save the caller's active tenant so we restore it after the request. In
    # production each request thread starts unscoped, so this is equivalent to
    # clearing — but it makes the middleware nestable (a test that has activated
    # a tenant via tenant_context() does not lose it across a client request).
    previous_tenant = get_current_tenant()
    try:
      if (
        user is not None
        and getattr(user, "is_authenticated", False)
        and not getattr(user, "is_superuser", False)
      ):
        tenant = getattr(user, "tenant", None)
        if tenant is not None:
          if not getattr(tenant, "is_active", True):
            # Deactivated tenant: end the session and bounce to login. The next
            # request arrives anonymous, so there is no redirect loop.
            logout(request)
            messages.error(request, _("This space has been deactivated and can no longer be accessed."))
            return redirect("members:login")
          request.tenant = tenant
          set_current_tenant(tenant)
          # database backstop: scope this connection's RLS policies
          set_rls_tenant(tenant.pk)
      elif getattr(user, "is_superuser", False):
        # platform admin: allowed to cross tenants (galleries policies honor it)
        set_rls_bypass(True)
      return self.get_response(request)
    finally:
      # Always clear both layers: a pooled connection must never carry a
      # stale tenant / bypass flag into the next request.
      reset_rls()
      set_current_tenant(previous_tenant)
