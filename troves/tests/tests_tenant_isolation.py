"""Tenant-isolation tests for troves (TenantModel).

Proves ``Trove`` honors the tenant-scoped manager: queryset isolation,
tenant auto-assignment, ``unscoped`` escape hatch, and the
default-tenant fallback when saving outside any tenant context.
"""

from django.test import TestCase

from core.utils import test_media_root_decorator
from members.tests.factories import MemberFactory
from tenants.models import Tenant
from tenants.scoping import set_current_tenant, tenant_context
from troves.models import Trove
from troves.tests.factories import TroveFactory


@test_media_root_decorator(__file__)
class TroveTenantIsolationTests(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.tenant_a = Tenant.objects.create(name="A", slug="t-trove-a")
    cls.tenant_b = Tenant.objects.create(name="B", slug="t-trove-b")
    cls.trove_a = TroveFactory(title="Trove", category="history", tenant=cls.tenant_a)
    cls.trove_b = TroveFactory(title="Trove", category="history", tenant=cls.tenant_b)

  def setUp(self):
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def test_queryset_isolation(self):
    with tenant_context(self.tenant_a):
      ids = set(Trove.objects.values_list("id", flat=True))
    self.assertIn(self.trove_a.id, ids)
    self.assertNotIn(self.trove_b.id, ids)

  def test_tenant_assigned_on_create(self):
    self.assertEqual(self.trove_a.tenant_id, self.tenant_a.id)
    self.assertEqual(self.trove_b.tenant_id, self.tenant_b.id)

  def test_unscoped_sees_all(self):
    ids = set(Trove.unscoped.values_list("id", flat=True))
    self.assertEqual(ids, {self.trove_a.id, self.trove_b.id})

  def test_save_without_tenant_falls_back_to_default(self):
    # e.g. a script creating a Trove outside any tenant_context: lands on default
    t = TroveFactory.build(tenant=None, owner=MemberFactory())
    t.save()
    self.assertEqual(t.tenant.slug, "default")
