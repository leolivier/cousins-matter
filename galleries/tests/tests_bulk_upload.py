from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from cm_main.utils import test_resource_full_path
from ..models import Gallery, Photo
from ..views import views_bulk
from .tests_utils import GalleryBaseTestCase


class TestBulkUpload(GalleryBaseTestCase):
  def setUp(self):
    # override the django-q settings to make the tasks run synchronously
    super().setUp()
    from django_q.conf import Conf
    self.old_sync = Conf.SYNC
    self.old_testing = Conf.TESTING
    Conf.SYNC = True
    Conf.TESTING = True

  def tearDown(self):
    super().tearDown()
    # restore the django-q settings
    from django_q.conf import Conf
    Conf.SYNC = self.old_sync
    Conf.TESTING = self.old_testing

  def test_bulk_upload(self):
    response = self.client.get(reverse('galleries:bulk_upload'))
    self.assertEqual(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, views_bulk.BulkUploadPhotosView)
    self.assertTemplateUsed(response, 'galleries/bulk_upload.html')

    zipfile = test_resource_full_path('test_bulk_import.zip', __file__)
    # print("zipfile:", zipfile)
    response = self.client.post(reverse('galleries:bulk_upload'),
                                {'zipfile': SimpleUploadedFile('test_bulk_import.zip', open(zipfile, 'rb').read(),
                                                               content_type='application/zip')},
                                follow=True)
    # self.print_response(response)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(Gallery.objects.count(), 3)
    self.assertEqual(Photo.objects.count(), 16)
    g = Gallery.objects.get(name='root-gallery')
    self.assertEqual(g.photo_set.count(), 7)
    g = Gallery.objects.get(name='sub gallery')
    self.assertEqual(g.photo_set.count(), 6)
    g = Gallery.objects.get(name='sub gallery #2')
    self.assertEqual(g.photo_set.count(), 3)
