"""RLS hardening for the tenant exports table.

Strict FOR ALL policy: an export (and its token) is invisible from another
tenant. The Q worker reads its own row through ``set_rls_bypass`` before it
activates the tenant. Idempotent, elidable, no-op outside PostgreSQL — same
shape as ``tenants.0010_rls_pages`` and friends.
"""

from django.db import migrations

from tenants.rls import strict_policy_sql

EXPORT_TABLES = ("tenants_tenantexport",)


def apply_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return  # SQLite dev: no RLS
  for table in EXPORT_TABLES:
    forward, _reverse = strict_policy_sql(table)
    schema_editor.execute(forward)


def revert_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return
  for table in reversed(EXPORT_TABLES):
    _forward, reverse = strict_policy_sql(table)
    schema_editor.execute(reverse)


class Migration(migrations.Migration):
  dependencies = [
    ("tenants", "0011_tenantexport"),
  ]

  operations = [
    migrations.RunPython(apply_rls, reverse_code=revert_rls, elidable=True),
  ]
