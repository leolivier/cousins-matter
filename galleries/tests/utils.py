from django.test import override_settings
from accounts.tests import LoggedAccountTestCase
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from PIL import Image
import sys
import os
import shutil


from galleries.models import Gallery, Photo


def test_file_full_path(image_file_basename):
  return os.path.join(os.path.dirname(__file__), 'resources', image_file_basename)


def create_image(image_file_basename):
  image_file = test_file_full_path(image_file_basename)
  membuf = BytesIO()
  with Image.open(image_file) as img:
    img.save(membuf, format='JPEG', quality=90)
    membuf.seek(0)
    size = sys.getsizeof(membuf)
    return InMemoryUploadedFile(membuf, 'ImageField', image_file_basename,
                                'image/jpeg', size, None)


# puts MEDIA_ROOT under the test directory during tests
TEST_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), "media")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class GalleryBaseTestCase(LoggedAccountTestCase):

  def setUp(self):
    super().setUp()

  def tearDown(self):
    super().tearDown()
    if os.path.isdir(TEST_MEDIA_ROOT):
      shutil.rmtree(TEST_MEDIA_ROOT)
    # print("deleted test media files")
    for gallery in Gallery.objects.filter(parent=None):
      gallery.delete()
    self.assertEqual(Gallery.objects.count(), 0)
    self.assertEqual(Photo.objects.count(), 0)
