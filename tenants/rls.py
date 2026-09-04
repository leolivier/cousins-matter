"""PostgreSQL row-level security wiring (defense-in-depth backstop).

The ORM tenant scoping (TenantManager / TenantMiddleware) is the primary
isolation layer; these policies are the database backstop for the runtime
(non-owner) role created by migration ``tenants.0003_rls``:

* pure TenantModel tables (galleries) get a strict ``FOR ALL`` policy — rows
  outside ``app.current_tenant_id`` are invisible AND unwritable;
* ``members_member`` gets split policies: permissive SELECT (login-by-email
  and cross-tenant admin lookups legitimately read before a tenant is known)
  but hard-scoped INSERT/UPDATE/DELETE;
* ``app.bypass = 'on'`` lets platform superusers administer cross-tenant.

The table owner (used for migrations) always bypasses RLS — never FORCE.
"""

from django.conf import settings

# Tables carrying a tenant_id column that get RLS policies. Extend this list
# when converting an app to TenantModel (chat, forum, polls, ...).
TENANT_RLS_TABLES: list[str] = [
  "members_member",
  "galleries_gallery",
  "galleries_photo",
]
# Strict FOR ALL policy (read AND write scoped to the session tenant).
TENANT_RLS_STRICT_TABLES: list[str] = [
  "galleries_gallery",
  "galleries_photo",
]
# Split policies: permissive SELECT + scoped writes.
TENANT_RLS_SPLIT_TABLES: list[str] = [
  "members_member",
]

_TENANT_PREDICATE = (
  "(tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::int OR current_setting('app.bypass', true) = 'on')"
)


def rls_enabled() -> bool:
  """Whether the runtime RLS session wiring should run."""
  return bool(
    getattr(settings, "MULTI_TENANT_ENABLED", False)
    and getattr(settings, "POSTGRES_RUNTIME_USER", None)
    and settings.DATABASES.get("default", {}).get("ENGINE", "").endswith("postgresql")
  )


def set_rls_tenant(tenant_id) -> None:
  """Set the session tenant for RLS policies (no-op when RLS is off)."""
  if not rls_enabled() or tenant_id is None:
    return
  from django.db import connection

  with connection.cursor() as cursor:
    cursor.execute("SET app.current_tenant_id = %s", [str(int(tenant_id))])


def set_rls_bypass(on: bool) -> None:
  """Escape hatch for platform superusers (no-op when RLS is off)."""
  if not rls_enabled():
    return
  from django.db import connection

  with connection.cursor() as cursor:
    cursor.execute("SET app.bypass = %s", ["on" if on else "off"])


def reset_rls() -> None:
  """Clear the RLS session variables (pooled connections must not leak them)."""
  if not rls_enabled():
    return
  from django.db import connection

  with connection.cursor() as cursor:
    cursor.execute("RESET app.current_tenant_id")
    cursor.execute("RESET app.bypass")
