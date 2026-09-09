"""RLS hardening for the classified_ads tables (app converted to TenantModel).

``classified_ads_classifiedad`` / ``classified_ads_adphoto`` are now
``TenantModel``-scoped in the ORM; give them the row-level-security
backstop. Idempotent, elidable, no-op outside PostgreSQL — same shape
as ``tenants.0003_rls`` and friends.
"""

from django.db import migrations

from tenants.rls import strict_policy_sql

ADS_TABLES = ("classified_ads_classifiedad", "classified_ads_adphoto")


def apply_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return  # SQLite dev: no RLS
  for table in ADS_TABLES:
    forward, _reverse = strict_policy_sql(table)
    schema_editor.execute(forward)


def revert_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return
  for table in reversed(ADS_TABLES):
    _forward, reverse = strict_policy_sql(table)
    schema_editor.execute(reverse)


class Migration(migrations.Migration):
  dependencies = [
    ("tenants", "0006_rls_forum"),
    # The ads tables must exist and carry tenant_id before the policies.
    ("classified_ads", "0004_tenant"),
  ]

  operations = [
    migrations.RunPython(apply_rls, reverse_code=revert_rls, elidable=True),
  ]
