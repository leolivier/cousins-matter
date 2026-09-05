"""RLS policy tests (catalog assertions + behavior with the runtime role).

The catalog part runs on any PostgreSQL deployment. The behavior part needs
POSTGRES_RUNTIME_USER/PASSWORD configured and a dedicated throwaway database,
so it is skipped unless the env is set (see docs/multi-tenancy.md).
"""

from django.db import connection
from django.test import TestCase, skipUnlessDBFeature

from tenants.rls import TENANT_RLS_SPLIT_TABLES, TENANT_RLS_STRICT_TABLES


@skipUnlessDBFeature("supports_transactions")
class RlsCatalogTests(TestCase):
  """The three tenant-scoped tables have RLS enabled (never forced) + policies."""

  def test_rls_enabled_never_forced(self):
    if connection.vendor != "postgresql":
      self.skipTest("postgresql only")
    with connection.cursor() as c:
      c.execute(
        "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class "
        "WHERE relname IN ('members_member','galleries_gallery','galleries_photo')"
      )
      rows = {r[0]: (r[1], r[2]) for r in c.fetchall()}
    for table in TENANT_RLS_STRICT_TABLES + TENANT_RLS_SPLIT_TABLES:
      self.assertIn(table, rows, table)
      self.assertTrue(rows[table][0], f"{table} must have RLS enabled")
      self.assertFalse(rows[table][1], f"{table} must NOT use FORCE (owner bypass is intended)")

  def test_policies_exist(self):
    if connection.vendor != "postgresql":
      self.skipTest("postgresql only")
    with connection.cursor() as c:
      c.execute("SELECT tablename, policyname FROM pg_policies WHERE schemaname='public'")
      policies = {(r[0], r[1]) for r in c.fetchall()}
    for table in TENANT_RLS_STRICT_TABLES:
      self.assertIn((table, "tenant_isolation"), policies)
    self.assertIn(("members_member", "tenant_read"), policies)
    self.assertIn(("members_member", "tenant_write"), policies)
    self.assertIn(("members_member", "tenant_update"), policies)
    self.assertIn(("members_member", "tenant_delete"), policies)
