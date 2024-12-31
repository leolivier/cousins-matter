from cousinsmatter.utils import test_media_root_decorator
from galleries.models import Gallery, Photo
from members.tests.tests_member_base import MemberTestCase


@test_media_root_decorator(__file__)
class GalleryBaseTestCase(MemberTestCase):

  def setUp(self):
    super().setUp()

  def tearDown(self):
    super().tearDown()
    for gallery in Gallery.objects.filter(parent=None):
      gallery.delete()
    self.assertEqual(Gallery.objects.count(), 0)
    self.assertEqual(Photo.objects.count(), 0)
