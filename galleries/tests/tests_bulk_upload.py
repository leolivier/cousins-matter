import os
from django.conf import settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Gallery, Photo
from ..views import views_bulk
from .utils import GalleryBaseTestCase, test_file_full_path

class TestBulkUpload(GalleryBaseTestCase):
	def test_bulk_upload(self):
		response = self.client.get(reverse('galleries:bulk_upload'))
		self.assertEqual(response.status_code, 200)
		self.assertIs(response.resolver_match.func.view_class, views_bulk.BulkUploadPhotosView)
		self.assertTemplateUsed(response, 'galleries/bulk_upload.html')

		zipfile = test_file_full_path('test_bulk_import.zip')
		response = self.client.post(reverse('galleries:bulk_upload'), 
															{ 'zipfile': SimpleUploadedFile('test_bulk_import.zip', open(zipfile, 'rb' ).read(), content_type='application/zip') }, 
															follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Gallery.objects.count(), 2)
		self.assertEqual(Photo.objects.count(), 4)
		for g in Gallery.objects.all():
			self.assertEqual(g.photo_set.count(), 2)