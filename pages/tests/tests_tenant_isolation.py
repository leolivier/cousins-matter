"""Tenant-isolation tests pages (TenantModel).

Proves ``pages.FlatPage`` (MTI child of ``django.contrib.flatpages``'
model) honors the tenant-scoped manager, that two tenants can own the
same page URL (the global ``django_flatpage`` unique dropped in
``pages.0004_tenant``), ``unscoped`` escape hatch, default-tenant
fallback, and that ``seed_tenant_pages`` gives each family its own
copy of the predefined pages.
"""

from django.test import TestCase

from pages.models import FlatPage
from pages.services import seed_tenant_pages
from pages.tests.factories import FlatPageFactory
from tenants.models import Tenant
from tenants.scoping import set_current_tenant, tenant_context


class PagesTenantIsolationTests(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.tenant_a = Tenant.objects.create(name="A", slug="t-pages-a")
    cls.tenant_b = Tenant.objects.create(name="B", slug="t-pages-b")
    cls.page_a = FlatPageFactory(tenant=cls.tenant_a, url="/home/authenticated/")
    cls.page_b = FlatPageFactory(tenant=cls.tenant_b, url="/home/authenticated/")

  def setUp(self):
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def test_queryset_isolation(self):
    with tenant_context(self.tenant_a):
      self.assertNotIn(self.page_b.id, set(FlatPage.objects.values_list("id", flat=True)))
      self.assertEqual(set(FlatPage.objects.values_list("url", flat=True)), {"/home/authenticated/"})
    with tenant_context(self.tenant_b):
      self.assertNotIn(self.page_a.id, set(FlatPage.objects.values_list("id", flat=True)))

  def test_same_url_in_two_tenants(self):
    # the global django_flatpage unique is gone; both rows coexist
    self.assertEqual(self.page_a.url, self.page_b.url)
    self.assertNotEqual(self.page_a.id, self.page_b.id)

  def test_unscoped(self):
    unscoped = set(FlatPage.unscoped.values_list("id", flat=True))
    self.assertIn(self.page_a.id, unscoped)
    self.assertIn(self.page_b.id, unscoped)

  def test_save_without_tenant_falls_back_to_default(self):
    page = FlatPageFactory.build(tenant=None)
    page.save()
    self.assertEqual(page.tenant.slug, Tenant.get_default().slug)

  def test_seed_tenant_pages_copies_predefined_pages(self):
    tenant = Tenant.objects.create(name="C", slug="t-pages-c")
    count = seed_tenant_pages(tenant)
    self.assertEqual(count, FlatPage.unscoped.filter(tenant=tenant).count())
    self.assertGreater(count, 0)
    with tenant_context(tenant):
      seeded = FlatPage.objects.filter(url="/fr/home/authenticated/").first()
    self.assertIsNotNone(seeded)
    self.assertTrue(seeded.predefined)
    self.assertFalse(seeded.updated)
    # default tenant's own copy is untouched (separate rows, same URL)
    self.assertNotEqual(seeded.id, FlatPage.unscoped.exclude(tenant=tenant).get(url="/fr/home/authenticated/").id)
