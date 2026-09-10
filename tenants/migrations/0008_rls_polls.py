"""RLS hardening for the polls tables (app converted to TenantModel).

Every polls table carrying a tenant column gets the row-level-security
backstop. MTI children (``polls_eventplanner``,
``polls_singleeventanswer``, ``polls_multieventanswer``) hold no tenant
column — reads join their scoped parent table.
Idempotent, elidable, no-op outside PostgreSQL — same shape as
``tenants.0003_rls`` and friends.
"""

from django.db import migrations

from tenants.rls import strict_policy_sql

POLLS_TABLES = (
  "polls_poll",
  "polls_question",
  "polls_pollanswer",
  "polls_yesnoanswer",
  "polls_textanswer",
  "polls_datetimeanswer",
  "polls_choiceanswer",
  "polls_multichoiceanswer",
)


def apply_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return  # SQLite dev: no RLS
  for table in POLLS_TABLES:
    forward, _reverse = strict_policy_sql(table)
    schema_editor.execute(forward)


def revert_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return
  for table in reversed(POLLS_TABLES):
    _forward, reverse = strict_policy_sql(table)
    schema_editor.execute(reverse)


class Migration(migrations.Migration):
  dependencies = [
    ("tenants", "0007_rls_classified_ads"),
    # The polls tables must exist and carry tenant_id before the policies.
    ("polls", "0005_tenant"),
  ]

  operations = [
    migrations.RunPython(apply_rls, reverse_code=revert_rls, elidable=True),
  ]
