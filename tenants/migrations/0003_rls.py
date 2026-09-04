"""PostgreSQL row-level security hardening (defense-in-depth backstop).

Creates (when configured) a non-owner runtime role and RLS policies on the
tenant-scoped tables, so that the web/qcluster processes — which connect with
that role when MULTI_TENANT_ENABLED + POSTGRES_RUNTIME_USER are set — cannot
cross tenants at the database level:

* strict ``FOR ALL`` policies on pure TenantModel tables (galleries): rows
  outside ``app.current_tenant_id`` are invisible and unwritable;
* split policies on ``members_member``: permissive SELECT (login-by-email and
  cross-tenant admin lookups read before a tenant is known) but hard-scoped
  INSERT/UPDATE/DELETE;
* ``app.bypass = 'on'`` lets platform superusers administer cross-tenant.

Notes:
* Runs as the table owner (migrations always do), which bypasses RLS — this is
  intended, and the reason we use ENABLE, never FORCE.
* When POSTGRES_RUNTIME_USER/PASSWORD are not configured, the role/grant part
  is skipped and only the inert ENABLE+policy statements run (policies are
  dead letters for the owner).
* Idempotent: every statement is DROP IF EXISTS / CREATE ROLE guarded.
"""
"""PostgreSQL row-level security hardening (defense-in-depth backstop).
...
"""

import re

from django.conf import settings
from django.db import migrations

from tenants.rls import TENANT_RLS_STRICT_TABLES, _TENANT_PREDICATE

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def qi(identifier: str) -> str:
    """Validate and quote a PostgreSQL identifier (role/table/schema name).

    Raises early on anything that isn't a plain [A-Za-z_][A-Za-z0-9_]* token,
    rather than silently building broken/dangerous SQL.
    """
    if not identifier or not _IDENTIFIER_RE.match(identifier):
        raise ValueError(f"Refusing to use invalid Postgres identifier: {identifier!r}")
    return '"' + identifier + '"'


def ql(value: str) -> str:
    """Quote a literal for embedding in DDL (no bind parameters there)."""
    return "'" + value.replace("'", "''") + "'"


def _build_sql() -> list[tuple[str, str | None]]:
    """Return the (forward, reverse) SQL statement pairs."""
    runtime_user = getattr(settings, "POSTGRES_RUNTIME_USER", None) or ""
    runtime_password = getattr(settings, "POSTGRES_RUNTIME_PASSWORD", None) or ""
    owner = settings.DATABASES["default"].get("USER", "cousinsmatter")
    sqls: list[tuple[str, str | None]] = []

    if runtime_user and runtime_password:
        user_ident = qi(runtime_user)
        owner_ident = qi(owner)

        # --- runtime role (idempotent) ---
        sqls.append((
            f"""
            DO $$
            BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {ql(runtime_user)}) THEN
                CREATE ROLE {user_ident} LOGIN PASSWORD {ql(runtime_password)} NOSUPERUSER NOCREATEDB NOCREATEROLE;
              ELSE
                ALTER ROLE {user_ident} LOGIN PASSWORD {ql(runtime_password)} NOSUPERUSER NOCREATEDB NOCREATEROLE;
              END IF;
            END
            $$;
            """,  # nosec B608 -- user_ident is validated against ^[A-Za-z_][A-Za-z0-9_]*$ by qi(); ql() escapes the literal
            f"DROP ROLE IF EXISTS {user_ident};",
        ))
        # --- grants (DML only: never CREATE/ALTER, DDL stays owner-only) ---
        grants = f"""
            GRANT USAGE ON SCHEMA public TO {user_ident};
            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {user_ident};
            GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {user_ident};
            ALTER DEFAULT PRIVILEGES IN SCHEMA public FOR ROLE {owner_ident}
              GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {user_ident};
            ALTER DEFAULT PRIVILEGES IN SCHEMA public FOR ROLE {owner_ident}
              GRANT USAGE, SELECT ON SEQUENCES TO {user_ident};
        """
        sqls.append((grants, f"REVOKE ALL ON SCHEMA public FROM {user_ident};"))

    # --- RLS policies (inert for the owner; active for the runtime role) ---
    for table in TENANT_RLS_STRICT_TABLES:
        table_ident = qi(table)
        sqls.append((
            f"""
            ALTER TABLE {table_ident} ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS tenant_isolation ON {table_ident};
            CREATE POLICY tenant_isolation ON {table_ident} FOR ALL
              USING {_TENANT_PREDICATE}
              WITH CHECK {_TENANT_PREDICATE};
            """,
            f"DROP POLICY IF EXISTS tenant_isolation ON {table_ident}; ALTER TABLE {table_ident} DISABLE ROW LEVEL SECURITY;",
        ))

    for table in ("members_member",):
        table_ident = qi(table)
        sqls.append((
            f"""
            ALTER TABLE {table_ident} ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS tenant_read ON {table_ident};
            DROP POLICY IF EXISTS tenant_write ON {table_ident};
            CREATE POLICY tenant_read ON {table_ident} FOR SELECT USING (true);
            CREATE POLICY tenant_write ON {table_ident} FOR INSERT WITH CHECK {_TENANT_PREDICATE};
            CREATE POLICY tenant_update ON {table_ident} FOR UPDATE
              USING {_TENANT_PREDICATE} WITH CHECK {_TENANT_PREDICATE};
            CREATE POLICY tenant_delete ON {table_ident} FOR DELETE USING {_TENANT_PREDICATE};
            """,
            f"""
            DROP POLICY IF EXISTS tenant_read ON {table_ident};
            DROP POLICY IF EXISTS tenant_write ON {table_ident};
            DROP POLICY IF EXISTS tenant_update ON {table_ident};
            DROP POLICY IF EXISTS tenant_delete ON {table_ident};
            ALTER TABLE {table_ident} DISABLE ROW LEVEL SECURITY;
            """,
        ))
    return sqls


def apply_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return  # SQLite dev: no RLS
    for forward, _reverse in _build_sql():
        schema_editor.execute(forward)


def revert_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    for _forward, reverse in reversed(_build_sql()):
        if reverse:
            schema_editor.execute(reverse)


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0002_seed_tenants"),
        # The RLS policies reference these tables: they must exist first.
        ("members", "0017_member_tenant_role"),
        ("galleries", "0007_tenant"),
    ]

    operations = [
        migrations.RunPython(apply_rls, reverse_code=revert_rls, elidable=True),
    ]
