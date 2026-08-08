from datetime import date

from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError

from .tests_utils import GalleryBaseTestCase
from core.utils import create_test_image
from galleries.models import Gallery, Photo


class TestGalleryMoves(GalleryBaseTestCase):
    def setUp(self):
        super().setUp()
        # Create gallery hierarchy:
        # rootA -> subA1 -> subA1_1
        # rootB
        self.rootA = Gallery(name="RootA")
        self.rootA.save()
        self.subA1 = Gallery(name="SubA1", parent=self.rootA)
        self.subA1.save()
        self.subA1_1 = Gallery(name="SubA1_1", parent=self.subA1)
        self.subA1_1.save()
        self.rootB = Gallery(name="RootB")
        self.rootB.save()
        self.image_file = create_test_image(__file__, "test-image-1.jpg")
        # Photos
        today = date.today()
        self.p_subA1 = Photo(name="p_subA1", gallery=self.subA1, date=today, image=self.image_file)
        self.p_subA1.save()
        self.p_subA1_1 = Photo(name="p_subA1_1", gallery=self.subA1_1, date=today, image=self.image_file)
        self.p_subA1_1.save()
        self.p_rootA = Photo(name="p_rootA", gallery=self.rootA, date=today, image=self.image_file)
        self.p_rootA.save()

    def tearDown(self):
        Gallery.objects.all().delete()
        Photo.objects.all().delete()
        return super().tearDown()

    def test_photo_gallery_change_moves_file(self):
        "Photo gallery change moves file"
        old_image_name = self.p_subA1.image.name
        old_thumb_name = self.p_subA1.thumbnail.name
        print(f"Photo created: image={old_image_name}, thumb={old_thumb_name}")
        self.assertTrue(default_storage.exists(old_image_name), f"old image does not exists {old_image_name}")
        if old_thumb_name:
            self.assertTrue(default_storage.exists(old_thumb_name), f"old thumb does not exists {old_thumb_name}")
        print(f"Gallery full_path subA1: {self.subA1.full_path()}")
        print(f"Gallery full_path rootB: {self.rootB.full_path()}")

        # Now move photo to rootB
        self.p_subA1.gallery = self.rootB
        self.p_subA1.save()
        self.p_subA1.refresh_from_db()
        new_image_name = self.p_subA1.image.name
        new_thumb_name = self.p_subA1.thumbnail.name
        print(f"After move: image={new_image_name}, thumb={new_thumb_name}")
        self.assertTrue(default_storage.exists(new_image_name), "new image does not exists after gallery change")
        self.assertFalse(default_storage.exists(old_image_name), "old image should be deleted")
        if old_thumb_name:
            # thumb was recreated, old should be gone, new should exist
            if new_thumb_name:
                self.assertTrue(default_storage.exists(new_thumb_name), "new thumb does not exists")
            self.assertFalse(default_storage.exists(old_thumb_name) and old_thumb_name != new_thumb_name,
                "old thumb should be deleted if different")

        self.assertTrue("RootB" in new_image_name or "rootb" in new_image_name.lower(),
            "new image path should contain new gallery slug")

    def test_gallery_parent_change_moves_subtree_photos(self):
        "Gallery parent change moves subtree photos"
        old_names = {
            'subA1_image': self.p_subA1.image.name,
            'subA1_thumb': self.p_subA1.thumbnail.name,
            'subA1_1_image': self.p_subA1_1.image.name,
            'subA1_1_thumb': self.p_subA1_1.thumbnail.name,
            'rootA_image': self.p_rootA.image.name,
        }
        # print("Before move:")
        # for k, v in old_names.items():
        #     print(f"  {k}: {v} exists={default_storage.exists(v)}")

        # old_subB_path = self.subA1.full_path()
        # old_subC_path = self.subA1_1.full_path()
        # print(f"self.subA1 full_path before: {old_subB_path}")
        # print(f"self.subA1_1 full_path before: {old_subC_path}")

        # Move self.subA1 from self.rootA to self.rootB
        self.subA1.parent = self.rootB
        self.subA1.save()
        self.subA1.refresh_from_db()
        self.subA1_1.refresh_from_db()
        # print(f"self.subA1 full_path after: {self.subA1.full_path()}")
        # print(f"self.subA1_1 full_path after: {self.subA1_1.full_path()}")

        self.p_subA1.refresh_from_db()
        self.p_subA1_1.refresh_from_db()
        self.p_rootA.refresh_from_db()

        new_names = {
            'subA1_image': self.p_subA1.image.name,
            'subA1_thumb': self.p_subA1.thumbnail.name,
            'subA1_1_image': self.p_subA1_1.image.name,
            'subA1_1_thumb': self.p_subA1_1.thumbnail.name,
            'rootA_image': self.p_rootA.image.name,
        }
        # print("After move:")
        # for k, v in new_names.items():
        #     print(f"  {k}: {v} exists={default_storage.exists(v)}")

        # Checks: self.subA1 and self.subA1_1 photos should have moved, self.rootA photo should NOT
        self.assertTrue(default_storage.exists(new_names['subA1_image']), "subA1 image should exists after move")
        self.assertFalse(default_storage.exists(old_names['subA1_image']), "subA1 old image should bedeleted")
        self.assertTrue(default_storage.exists(new_names['subA1_1_image']), "subA1_1 image should exists after move")
        self.assertFalse(default_storage.exists(old_names['subA1_1_image']), "subA1_1 old image should bedeleted")
        # self.rootA photo should stay
        self.assertTrue(default_storage.exists(new_names['rootA_image']), "rootA image should still exists")
        self.assertTrue(old_names['rootA_image'] == new_names['rootA_image'], "rootA image should remain unchanged")

        # Check paths contain new parent slug
        self.assertTrue("rootb" in new_names['subA1_image'].lower(), "subA1 new path should contain rootB")
        self.assertTrue("rootb" in new_names['subA1_1_image'].lower(), "subA1_1 new path should contain rootB")

        # Thumbnails also moved
        if old_names['subA1_thumb']:
            self.assertTrue(default_storage.exists(new_names['subA1_thumb']), "subA1 thumb should be moved")
            if old_names['subA1_thumb'] != new_names['subA1_thumb']:
                self.assertFalse(default_storage.exists(old_names['subA1_thumb']), "subA1 old thumb should be deleted")
        if old_names['subA1_1_thumb']:
            self.assertTrue(default_storage.exists(new_names['subA1_1_thumb']), "subA1_1 thumb should be moved")
            if old_names['subA1_1_thumb'] != new_names['subA1_1_thumb']:
                self.assertFalse(default_storage.exists(old_names['subA1_1_thumb']), "subA1_1 old thumb should be deleted")

    def test_gallery_move_with_no_photos(self):
        "Gallery move with no photos (should not error)"
        empty_gallery = Gallery(name="Empty", parent=self.rootA)
        empty_gallery.save()
        empty_gallery.parent = self.rootB
        empty_gallery.save()
        # print("PASS: empty gallery move succeeded")

    def test_photo_gallery_change_to_none(self):
        "Photo gallery change to None should fail validation (no move)"
        self.p_subA1.gallery = None
        with self.assertRaises(ValidationError):
            self.p_subA1.save()
