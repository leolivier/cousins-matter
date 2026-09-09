"""PostgreSQL row-level security wiring (defense-in-depth backstop).

The ORM tenant scoping (TenantManager / TenantMiddleware) is the primary
isolation layer; these policies are the database backstop for the runtime
(non-owner) role created by migration ``tenants.0003_rls``:

* pure TenantModel tables (galleries, chat) get a strict ``FOR ALL`` policy —
  rows outside ``app.current_tenant_id`` are invisible AND unwritable;
* ``members_member`` gets split policies: permissive SELECT (login-by-email
  and cross-tenant admin lookups legitimately read before a tenant is known)
  but hard-scoped INSERT/UPDATE/DELETE;
* ``app.bypass = 'on'`` lets platform superusers administer cross-tenant.

The table owner (used for migrations) always bypasses RLS — never FORCE.
"""

import re

from django.conf import settings

# Tables carrying a tenant_id column that get RLS policies. Extend this list
# when converting an app to TenantModel (polls, pages, genealogy, ...).
TENANT_RLS_TABLES: list[str] = [
  "members_member",
  "galleries_gallery",
  "galleries_photo",
  "chat_chatroom",
  "chat_chatmessage",
  "troves_trove",
  "forum_message",
  "forum_post",
  "forum_comment",
  "classified_ads_classifiedad",
  "classified_ads_adphoto",
]
# Strict FOR ALL policy (read AND write scoped to the session tenant).
TENANT_RLS_STRICT_TABLES: list[str] = [
  "galleries_gallery",
  "galleries_photo",
  "chat_chatroom",
  "chat_chatmessage",
  "troves_trove",
  "forum_message",
  "forum_post",
  "forum_comment",
  "classified_ads_classifiedad",
  "classified_ads_adphoto",
]
# Split policies: permissive SELECT + scoped writes.
TENANT_RLS_SPLIT_TABLES: list[str] = [
  "members_member",
]

_TENANT_PREDICATE = (
  "(tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::int OR current_setting('app.bypass', true) = 'on')"
)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def qi(identifier: str) -> str:
  """Validate + quote a PostgreSQL identifier (table/schema/role name).

  Raises early on anything that is not a plain [A-Za-z_][A-Za-z0-9_]* token,
  rather than emitting broken/dangerous SQL.
  """
  if not _IDENTIFIER_RE.match(identifier):
    raise ValueError(f"Refusing to quote suspicious identifier: {identifier!r}")
  return f'"{identifier}"'


def strict_policy_sql(table: str) -> tuple[str, str]:
  """Return ``(forward, reverse)`` DDL for the strict ``FOR ALL`` tenant policy.

  Shared by the RLS migrations (``tenants.0003_rls`` and the per-app
  hardening ones extending coverage to newly converted apps).
  """
  ident = qi(table)
  return (
    f"""
ALTER TABLE {ident} ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON {ident};
CREATE POLICY tenant_isolation ON {ident} FOR ALL
  USING {_TENANT_PREDICATE}
  WITH CHECK {_TENANT_PREDICATE};
""",
    f"""
DROP POLICY IF EXISTS tenant_isolation ON {ident};
ALTER TABLE {ident} DISABLE ROW LEVEL SECURITY;
""",
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
