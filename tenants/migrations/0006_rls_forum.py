"""RLS hardening for the forum tables (app converted to TenantModel).

``forum_message`` / ``forum_post`` / ``forum_comment`` are now
``TenantModel``-scoped in the ORM; give them the row-level-security
backstop. Idempotent, elidable, no-op outside PostgreSQL — same shape
as ``tenants.0003_rls`` and friends.
"""

from django.db import migrations

from tenants.rls import strict_policy_sql

FORUM_TABLES = ("forum_message", "forum_post", "forum_comment")


def apply_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return  # SQLite dev: no RLS
  for table in FORUM_TABLES:
    forward, _reverse = strict_policy_sql(table)
    schema_editor.execute(forward)


def revert_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return
  for table in reversed(FORUM_TABLES):
    _forward, reverse = strict_policy_sql(table)
    schema_editor.execute(reverse)


class Migration(migrations.Migration):
  dependencies = [
    ("tenants", "0005_rls_troves"),
    # The forum tables must exist and carry tenant_id before the policies.
    ("forum", "0007_tenant"),
  ]

  operations = [
    migrations.RunPython(apply_rls, reverse_code=revert_rls, elidable=True),
  ]
