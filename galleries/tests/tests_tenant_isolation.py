"""Tenant-isolation tests for the galleries vertical slice (TenantModel).

Proves that ``Gallery`` (the first ``TenantModel`` subclass) honors the
tenant-scoped manager: queryset isolation, ``(tenant, slug, parent)``
uniqueness allows the same slug in two tenants, the ``unscoped`` escape hatch
works, and saving without a current tenant raises.
"""

from django.test import TestCase

from galleries.models import Gallery
from tenants.models import Tenant
from tenants.scoping import set_current_tenant, tenant_context


class GalleryTenantIsolationTests(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.tenant_a = Tenant.objects.create(name="A", slug="g-tenant-a")
    cls.tenant_b = Tenant.objects.create(name="B", slug="g-tenant-b")
    with tenant_context(cls.tenant_a):
      cls.gallery_a = Gallery.objects.create(name="Holiday")
    with tenant_context(cls.tenant_b):
      cls.gallery_b = Gallery.objects.create(name="Holiday")  # same name, other tenant

  def setUp(self):
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def test_queryset_isolation(self):
    with tenant_context(self.tenant_a):
      ids = set(Gallery.objects.values_list("id", flat=True))
    self.assertIn(self.gallery_a.id, ids)
    self.assertNotIn(self.gallery_b.id, ids)

  def test_same_slug_two_tenants_succeeds(self):
    # the uniqueness constraint is (tenant, slug, parent), not slug alone
    self.assertEqual(self.gallery_a.slug, self.gallery_b.slug)
    self.assertNotEqual(self.gallery_a.tenant_id, self.gallery_b.tenant_id)
    self.assertIsNotNone(self.gallery_a.tenant_id)

  def test_unscoped_sees_all(self):
    same_slug = Gallery.unscoped.filter(slug=self.gallery_a.slug)
    self.assertEqual({g.id for g in same_slug}, {self.gallery_a.id, self.gallery_b.id})

  def test_tenant_assigned_on_create(self):
    with tenant_context(self.tenant_b):
      g = Gallery.objects.create(name="Private B")
    self.assertEqual(g.tenant_id, self.tenant_b.id)

  def test_save_without_tenant_raises(self):
    g = Gallery(name="Orphan")
    with self.assertRaises(ValueError):
      g.save()
