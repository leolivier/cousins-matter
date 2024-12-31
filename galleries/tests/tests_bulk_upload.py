from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from cousinsmatter.utils import test_resource_full_path
from ..models import Gallery, Photo
from ..views import views_bulk
from .tests_utils import GalleryBaseTestCase


class TestBulkUpload(GalleryBaseTestCase):
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
    self.assertEqual(Gallery.objects.count(), 2)
    self.assertEqual(Photo.objects.count(), 4)
    for g in Gallery.objects.all():
      self.assertEqual(g.photo_set.count(), 2)
