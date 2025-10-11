from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from cm_main.tests.test_django_q import django_q_sync_class
from cm_main.utils import test_resource_full_path
from ..models import Gallery, Photo
from ..views import views_bulk
from .tests_utils import GalleryBaseTestCase


@django_q_sync_class
class TestBulkUpload(GalleryBaseTestCase):

  def test_bulk_upload(self):
    """Tests bulk uploading photos."""
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
