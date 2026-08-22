"""Tenant-aware cache-key helper for the shared-schema deployment.

Prefixing cache keys with the tenant keeps per-tenant computed values (charts,
feature sets, ...) from leaking across tenants. Returns the key unchanged when
no tenant is active (platform admin, management commands, anonymous request).

Apply with ``cache.set(tenant_cache_key("..."), ...)`` when converting an app
to multi-tenant (e.g. the genealogy chart caches).
"""

from .scoping import get_current_tenant


def tenant_cache_key(key: str) -> str:
  """Prefix ``key`` with the active tenant (``"t:<id>:<key>"``).

  Returns the key unchanged when no tenant is active.
  """
  tenant = get_current_tenant()
  if tenant is None:
    return key
  return f"t:{tenant.pk}:{key}"
