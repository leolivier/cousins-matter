"""RLS hardening for the troves table (app converted to TenantModel).

``troves_trove`` is now ``TenantModel``-scoped in the ORM; give it the
row-level-security backstop. Idempotent, elidable, no-op outside
PostgreSQL — same shape as ``tenants.0003_rls`` / ``tenants.0004_rls_chat``.
"""

from django.db import migrations

from tenants.rls import strict_policy_sql

TROVES_TABLES = ("troves_trove",)


def apply_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return  # SQLite dev: no RLS
  for table in TROVES_TABLES:
    forward, _reverse = strict_policy_sql(table)
    schema_editor.execute(forward)


def revert_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return
  for table in reversed(TROVES_TABLES):
    _forward, reverse = strict_policy_sql(table)
    schema_editor.execute(reverse)


class Migration(migrations.Migration):
  dependencies = [
    ("tenants", "0004_rls_chat"),
    # The troves table must exist and carry tenant_id before the policy.
    ("troves", "0005_tenant"),
  ]

  operations = [
    migrations.RunPython(apply_rls, reverse_code=revert_rls, elidable=True),
  ]
