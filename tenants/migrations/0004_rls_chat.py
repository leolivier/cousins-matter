"""RLS hardening for the chat tables (closing the known gap after PR #457).

``chat_chatroom`` / ``chat_chatmessage`` are ``TenantModel``-scoped in the ORM
but had no row-level-security backstop. Idempotent, elidable, no-op outside
PostgreSQL — same shape as ``tenants.0003_rls``, restricted to the chat tables.
"""

from django.db import migrations

from tenants.rls import strict_policy_sql

CHAT_TABLES = ("chat_chatroom", "chat_chatmessage")


def apply_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return  # SQLite dev: no RLS
  for table in CHAT_TABLES:
    forward, _reverse = strict_policy_sql(table)
    schema_editor.execute(forward)


def revert_rls(apps, schema_editor):
  if schema_editor.connection.vendor != "postgresql":
    return
  for table in reversed(CHAT_TABLES):
    _forward, reverse = strict_policy_sql(table)
    schema_editor.execute(reverse)


class Migration(migrations.Migration):
  dependencies = [
    ("tenants", "0003_rls"),
    # The chat tables must exist before policies can be created on them.
    ("chat", "0010_remove_chatmessage_chat_chatme_room_id_95b551_idx_and_more"),
  ]

  operations = [
    migrations.RunPython(apply_rls, reverse_code=revert_rls, elidable=True),
  ]
