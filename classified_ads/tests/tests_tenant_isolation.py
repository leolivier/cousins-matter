"""Tenant-isolation tests for classified ads (TenantModel).

Proves ``ClassifiedAd``/``AdPhoto`` honor the tenant-scoped manager:
queryset isolation, tenant auto-assignment, ``unscoped`` escape hatch,
and the default-tenant fallback when saving outside any tenant context.
"""

from django.test import TestCase

from classified_ads.models import AdPhoto, ClassifiedAd
from classified_ads.tests.factories import ClassifiedAdFactory
from members.tests.factories import MemberFactory
from tenants.models import Tenant
from tenants.scoping import set_current_tenant, tenant_context


class ClassifiedAdTenantIsolationTests(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.tenant_a = Tenant.objects.create(name="A", slug="t-ads-a")
    cls.tenant_b = Tenant.objects.create(name="B", slug="t-ads-b")
    cls.ad_a = ClassifiedAdFactory(tenant=cls.tenant_a)
    cls.ad_b = ClassifiedAdFactory(tenant=cls.tenant_b)

  def setUp(self):
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def test_queryset_isolation(self):
    with tenant_context(self.tenant_a):
      ad_ids = set(ClassifiedAd.objects.values_list("id", flat=True))
      photo_ids = set(AdPhoto.objects.values_list("id", flat=True))
    self.assertEqual(ad_ids, {self.ad_a.id})
    self.assertEqual(photo_ids, {p.id for p in self.ad_a.photos.all()})

  def test_tenant_assigned_on_create(self):
    ad = ClassifiedAdFactory(tenant=self.tenant_b)
    self.assertEqual(ad.tenant_id, self.tenant_b.id)
    # photos always inherit their ad's tenant
    self.assertTrue(ad.photos.exists())
    self.assertEqual(ad.photos.first().tenant_id, self.tenant_b.id)

  def test_unscoped_sees_all(self):
    self.assertEqual(set(ClassifiedAd.unscoped.values_list("id", flat=True)), {self.ad_a.id, self.ad_b.id})

  def test_save_without_tenant_falls_back_to_default(self):
    # e.g. a script creating an ad outside any tenant_context: lands on default
    ad = ClassifiedAdFactory.build(tenant=None, owner=MemberFactory())
    ad.save()
    self.assertEqual(ad.tenant.slug, "default")
