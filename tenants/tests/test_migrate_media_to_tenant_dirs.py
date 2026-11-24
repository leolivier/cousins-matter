from datetime import date
from io import StringIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.test import TestCase, override_settings

from classified_ads.models import AdPhoto, ClassifiedAd
from core.utils import test_media_root_decorator
from galleries.models import Gallery, Photo
from members.models import Member
from tenants.models import Tenant
from troves.models import Trove

SLUG = "mig"


def run(dry_run=False):
  out = StringIO()
  call_command("migrate_media_to_tenant_dirs", *(["--dry-run"] if dry_run else []), stdout=out, stderr=StringIO())
  return out.getvalue()


@test_media_root_decorator(__file__)
@override_settings(MULTI_TENANT_ENABLED=True)
class MigrateMediaToTenantDirsTestCase(TestCase):
  def setUp(self):
    self.tenant = Tenant.objects.create(name="Mig", slug=SLUG)
    self.member = Member(username="mig-user", email="mig@example.com", tenant=self.tenant, avatar="avatars/a.jpg")
    Member.unscoped.bulk_create([self.member])

    self.gallery = Gallery(name="G", slug="g", tenant=self.tenant)
    Gallery.unscoped.bulk_create([self.gallery])
    self.photo = Photo(
      image="galleries/g/a.jpg",
      thumbnail="galleries/g/thumbnails/a.webp",
      gallery=self.gallery,
      tenant=self.tenant,
      date=date(2020, 1, 1),
      slug="a",
    )
    Photo.unscoped.bulk_create([self.photo])

    self.ad = ClassifiedAd(
      title="Ad",
      category="misc",
      subcategory="misc",
      description="d",
      price="1",
      owner=self.member,
      tenant=self.tenant,
    )
    ClassifiedAd.unscoped.bulk_create([self.ad])
    self.ad_photo_name = f"classified_ads/{self.ad.pk}/a.jpg"
    self.ad_photo = AdPhoto(image=self.ad_photo_name, thumbnail=self.ad_photo_name, ad=self.ad, tenant=self.tenant)
    AdPhoto.unscoped.bulk_create([self.ad_photo])

    self.trove = Trove(
      title="T",
      category="miscellaneous",
      owner=self.member,
      tenant=self.tenant,
      picture="troves/pictures/a.jpg",
      thumbnail="troves/pictures/a.jpg",
      file="troves/files/f.txt",
    )
    Trove.unscoped.bulk_create([self.trove])

    for name in (
      "galleries/g/a.jpg",
      "galleries/g/thumbnails/a.webp",
      "avatars/a.jpg",
      "avatars/mini_a.jpg",
      self.ad_photo_name,
      "troves/pictures/a.jpg",
      "troves/files/f.txt",
    ):
      default_storage.save(name, ContentFile(b"x"))

  def _refresh(self):
    return (
      Photo.unscoped.get(pk=self.photo.pk),
      Member.unscoped.get(pk=self.member.pk),
      AdPhoto.unscoped.get(pk=self.ad_photo.pk),
      Trove.unscoped.get(pk=self.trove.pk),
    )

  def test_dry_run_changes_nothing(self):
    output = run(dry_run=True)
    self.assertIn("would move", output)
    photo, member, ad_photo, trove = self._refresh()
    self.assertEqual(photo.image.name, "galleries/g/a.jpg")
    self.assertEqual(member.avatar.name, "avatars/a.jpg")
    self.assertEqual(ad_photo.image.name, self.ad_photo_name)
    self.assertEqual(trove.picture.name, "troves/pictures/a.jpg")
    self.assertTrue(default_storage.exists("galleries/g/a.jpg"))

  def test_migrates_every_target(self):
    run()
    photo, member, ad_photo, trove = self._refresh()
    self.assertEqual(photo.image.name, f"{SLUG}/galleries/g/a.jpg")
    self.assertEqual(photo.thumbnail.name, f"{SLUG}/galleries/g/thumbnails/a.webp")
    self.assertEqual(member.avatar.name, f"{SLUG}/avatars/a.jpg")
    self.assertEqual(ad_photo.image.name, f"{SLUG}/{self.ad_photo_name}")
    self.assertEqual(ad_photo.thumbnail.name, f"{SLUG}/{self.ad_photo_name}")
    self.assertEqual(trove.picture.name, f"{SLUG}/troves/pictures/a.jpg")
    self.assertEqual(trove.thumbnail.name, f"{SLUG}/troves/pictures/a.jpg")
    self.assertEqual(trove.file.name, f"{SLUG}/troves/files/f.txt")

    for new_name in (
      f"{SLUG}/galleries/g/a.jpg",
      f"{SLUG}/galleries/g/thumbnails/a.webp",
      f"{SLUG}/avatars/a.jpg",
      f"{SLUG}/avatars/mini_a.jpg",
      f"{SLUG}/{self.ad_photo_name}",
      f"{SLUG}/troves/pictures/a.jpg",
      f"{SLUG}/troves/files/f.txt",
    ):
      self.assertTrue(default_storage.exists(new_name), new_name)
    for old_name in ("galleries/g/a.jpg", "avatars/a.jpg", "avatars/mini_a.jpg", self.ad_photo_name):
      self.assertFalse(default_storage.exists(old_name), old_name)

  def test_is_idempotent(self):
    run()
    output = run()
    self.assertIn("moved 0 file(s)", output)

  @override_settings(MULTI_TENANT_ENABLED=False)
  def test_does_nothing_in_mono_tenant_mode(self):
    output = run()
    self.assertIn("nothing to migrate", output)
    photo, member, _, _ = self._refresh()
    self.assertEqual(photo.image.name, "galleries/g/a.jpg")
    self.assertEqual(member.avatar.name, "avatars/a.jpg")
