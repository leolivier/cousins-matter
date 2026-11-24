from django.test import TestCase, override_settings

from classified_ads.models import AdPhoto, get_photo_path, get_thumbnail_path
from galleries.models import Gallery, Photo, photo_path, thumbnail_path
from members.models import Member, avatar_path
from tenants.models import Tenant
from tenants.scoping import tenant_context
from tenants.storage import tenant_prefix
from troves.models import Trove
from troves.models import file_path as trove_file_path
from troves.models import picture_path as trove_picture_path
from troves.models import thumbnail_path as trove_thumbnail_path


@override_settings(MULTI_TENANT_ENABLED=False)
class MonoTenantPathsTestCase(TestCase):
  """Flag off (self-hosted mono-tenant): upload paths must stay exactly as before."""

  def setUp(self):
    self.tenant = Tenant(name="Fam", slug="fam")
    self.gallery = Gallery.objects.create(name="G", slug="g")
    self.photo = Photo(gallery=self.gallery, tenant=self.tenant)
    self.avatar_owner = Member(tenant=self.tenant)
    self.ad_photo = AdPhoto(tenant=self.tenant, ad_id=7)
    self.trove = Trove(tenant=self.tenant)

  def test_tenant_prefix_is_empty(self):
    self.assertEqual(tenant_prefix(self.photo), "")

  def test_paths_are_unchanged(self):
    self.assertEqual(photo_path(self.photo, "a.jpg"), "galleries/g/a.jpg")
    self.assertEqual(thumbnail_path(self.photo, "a.jpg"), "galleries/g/thumbnails/a.jpg")
    self.assertEqual(avatar_path(self.avatar_owner, "a.jpg"), "avatars/a.jpg")
    self.assertEqual(get_photo_path(self.ad_photo, "a.jpg"), "classified_ads/7/a.jpg")
    self.assertEqual(get_thumbnail_path(self.ad_photo, "a.jpg"), "classified_ads/7/thumbnails/a.jpg")
    self.assertEqual(trove_picture_path(self.trove, "a.jpg"), "troves/pictures/a.jpg")
    self.assertEqual(trove_thumbnail_path(self.trove, "a.jpg"), "troves/pictures/thumbnails/a.jpg")
    self.assertEqual(trove_file_path(self.trove, "a.txt"), "troves/files/a.txt")


@override_settings(MULTI_TENANT_ENABLED=True)
class MultiTenantPathsTestCase(TestCase):
  """Flag on: every protected path is prefixed with the tenant slug."""

  @classmethod
  def setUpTestData(cls):
    cls.tenant = Tenant.objects.create(name="Fam", slug="path-fam")

  def setUp(self):
    self.gallery = Gallery.objects.create(name="G", slug="g", tenant=self.tenant)
    self.photo = Photo(gallery=self.gallery, tenant=self.tenant)
    self.avatar_owner = Member(tenant=self.tenant)
    self.ad_photo = AdPhoto(tenant=self.tenant, ad_id=7)
    self.trove = Trove(tenant=self.tenant)

  def test_tenant_prefix_uses_instance_tenant(self):
    self.assertEqual(tenant_prefix(self.photo), "path-fam")

  def test_paths_are_tenant_prefixed(self):
    self.assertEqual(photo_path(self.photo, "a.jpg"), "path-fam/galleries/g/a.jpg")
    self.assertEqual(thumbnail_path(self.photo, "a.jpg"), "path-fam/galleries/g/thumbnails/a.jpg")
    self.assertEqual(avatar_path(self.avatar_owner, "a.jpg"), "path-fam/avatars/a.jpg")
    self.assertEqual(get_photo_path(self.ad_photo, "a.jpg"), "path-fam/classified_ads/7/a.jpg")
    self.assertEqual(get_thumbnail_path(self.ad_photo, "a.jpg"), "path-fam/classified_ads/7/thumbnails/a.jpg")
    self.assertEqual(trove_picture_path(self.trove, "a.jpg"), "path-fam/troves/pictures/a.jpg")
    self.assertEqual(trove_thumbnail_path(self.trove, "a.jpg"), "path-fam/troves/pictures/thumbnails/a.jpg")
    self.assertEqual(trove_file_path(self.trove, "a.txt"), "path-fam/troves/files/a.txt")

  def test_prefix_falls_back_to_current_tenant(self):
    with tenant_context(self.tenant):
      self.assertEqual(tenant_prefix(Member()), "path-fam")

  def test_prefix_falls_back_to_default_tenant(self):
    self.assertEqual(tenant_prefix(Member()), Tenant.get_default().slug)
