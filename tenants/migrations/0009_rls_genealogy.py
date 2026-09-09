"""RLS hardening for the genealogy tables (app converted to TenantModel).

Idempotent, elidable, no-op outside PostgreSQL — same shape as
``tenants.0008_rls_polls`` and friends.
"""

from django.db import migrations

from tenants.rls import strict_policy_sql

GENEALOGY_TABLES = (
  "genealogy_person",
  "genealogy_family",
)


def apply_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return  # SQLite dev: no RLS
  for table in GENEALOGY_TABLES:
    forward, _reverse = strict_policy_sql(table)
    schema_editor.execute(forward)


def revert_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return
  for table in reversed(GENEALOGY_TABLES):
    _forward, reverse = strict_policy_sql(table)
    schema_editor.execute(reverse)


class Migration(migrations.Migration):
  dependencies = [
    ("tenants", "0008_rls_polls"),
    # The genealogy tables must exist and carry tenant_id before the policies.
    ("genealogy", "0004_tenant"),
  ]

  operations = [
    migrations.RunPython(apply_rls, reverse_code=revert_rls, elidable=True),
  ]
