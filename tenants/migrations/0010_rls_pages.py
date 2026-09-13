"""RLS hardening for the pages table (app converted to TenantModel).

Only ``pages_flatpage`` (the MTI child carrying the tenant column) is
scoped; the parent ``django_flatpage`` stays global — reads go through
the child-scoped manager. Idempotent, elidable, no-op outside
PostgreSQL — same shape as ``tenants.0009_rls_genealogy`` and friends.
"""

from django.db import migrations

from tenants.rls import strict_policy_sql

PAGES_TABLES = ("pages_flatpage",)


def apply_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return  # SQLite dev: no RLS
  for table in PAGES_TABLES:
    forward, _reverse = strict_policy_sql(table)
    schema_editor.execute(forward)


def revert_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return
  for table in reversed(PAGES_TABLES):
    _forward, reverse = strict_policy_sql(table)
    schema_editor.execute(reverse)


class Migration(migrations.Migration):
  dependencies = [
    ("tenants", "0009_rls_genealogy"),
    # The pages table must exist and carry tenant_id before the policies.
    ("pages", "0004_tenant"),
  ]

  operations = [
    migrations.RunPython(apply_rls, reverse_code=revert_rls, elidable=True),
  ]
