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

from django.conf import settings
from django.db import migrations

from tenants.rls import TENANT_RLS_STRICT_TABLES, _TENANT_PREDICATE


def _build_sql() -> list[tuple[str, str | None]]:
    """Return the (forward, reverse) SQL statement pairs."""
    runtime_user = getattr(settings, "POSTGRES_RUNTIME_USER", None) or ""
    runtime_password = getattr(settings, "POSTGRES_RUNTIME_PASSWORD", None) or ""
    owner = settings.DATABASES["default"].get("USER", "cousinsmatter")
    sqls: list[tuple[str, str | None]] = []

    if runtime_user and runtime_password:
        # --- runtime role (idempotent) ---
        sqls.append((
            f"""
            DO $$
            BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{runtime_user}') THEN
                CREATE ROLE {runtime_user} LOGIN PASSWORD {ql(runtime_password)} NOSUPERUSER NOCREATEDB NOCREATEROLE;
              ELSE
                ALTER ROLE {runtime_user} LOGIN PASSWORD {ql(runtime_password)} NOSUPERUSER NOCREATEDB NOCREATEROLE;
              END IF;
            END
            $$;
            """,
            f"DROP ROLE IF EXISTS {runtime_user};",
        ))
        # --- grants (DML only: never CREATE/ALTER, DDL stays owner-only) ---
        grants = f"""
            GRANT USAGE ON SCHEMA public TO {runtime_user};
            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {runtime_user};
            GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {runtime_user};
            ALTER DEFAULT PRIVILEGES IN SCHEMA public FOR ROLE {owner}
              GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {runtime_user};
            ALTER DEFAULT PRIVILEGES IN SCHEMA public FOR ROLE {owner}
              GRANT USAGE, SELECT ON SEQUENCES TO {runtime_user};
        """
        sqls.append((grants, f"REVOKE ALL ON SCHEMA public FROM {runtime_user};"))

    # --- RLS policies (inert for the owner; active for the runtime role) ---
    for table in TENANT_RLS_STRICT_TABLES:
        sqls.append((
            f"""
            ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS tenant_isolation ON {table};
            CREATE POLICY tenant_isolation ON {table} FOR ALL
              USING {_TENANT_PREDICATE}
              WITH CHECK {_TENANT_PREDICATE};
            """,
            f"DROP POLICY IF EXISTS tenant_isolation ON {table}; ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;",
        ))

    for table in ("members_member",):
        sqls.append((
            f"""
            ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS tenant_read ON {table};
            DROP POLICY IF EXISTS tenant_write ON {table};
            CREATE POLICY tenant_read ON {table} FOR SELECT USING (true);
            CREATE POLICY tenant_write ON {table} FOR INSERT WITH CHECK {_TENANT_PREDICATE};
            CREATE POLICY tenant_update ON {table} FOR UPDATE
              USING {_TENANT_PREDICATE} WITH CHECK {_TENANT_PREDICATE};
            CREATE POLICY tenant_delete ON {table} FOR DELETE USING {_TENANT_PREDICATE};
            """,
            f"""
            DROP POLICY IF EXISTS tenant_read ON {table};
            DROP POLICY IF EXISTS tenant_write ON {table};
            DROP POLICY IF EXISTS tenant_update ON {table};
            DROP POLICY IF EXISTS tenant_delete ON {table};
            ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;
            """,
        ))
    return sqls


def ql(value: str) -> str:
    """Quote a literal for embedding in DDL (no bind parameters there)."""
    return "'" + value.replace("'", "''") + "'"


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
    ]

    operations = [
        migrations.RunPython(apply_rls, reverse_code=revert_rls, elidable=True),
    ]
