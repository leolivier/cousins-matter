# import shutil
import urllib.parse
from django.conf import settings
from django.urls import reverse
from django.http import StreamingHttpResponse
# from django.core.files.storage import FileSystemStorage, default_storage
from django.core.files.storage import default_storage

from cm_main.utils import test_resource_full_path, get_test_absolute_url
from members.tests.tests_member_base import MemberTestCase
from cm_main.utils import storage_rmtree


class ProtectedMediaTestCase(MemberTestCase):
  def setUp(self):
    super().setUp()
    # use test logo from resources as an image file to test the protected media
    # so copy it to /media/testdir/testimage.png
    self.storage = default_storage
    # absolute_name = isinstance(self.storage, FileSystemStorage)
    # self.test_file = settings.MEDIA_ROOT if absolute_name else settings.MEDIA_REL
    # self.test_file = self.test_file / 'test_protected_media' / 'test_image.jpg'
    self.test_file = settings.MEDIA_REL / 'test_protected_media' / 'test_image.jpg'
    logo_file = test_resource_full_path('test-logo.jpg', __file__)
    # Make sure the destination directory exists
    # useless with storage storage.mkdir(self.test_file.parent)
    # Copy the test resource
    # manage differently with storage  shutil.copy2(logo_file, self.test_file)
    with open(logo_file, 'rb') as initial_file:
      self.storage.save(self.test_file, initial_file)
    with open(logo_file, 'rb') as initial_file:  # reopen as save above closes the file
      self.uploaded_content = initial_file.read()

    # self.rel_path = str(self.test_file.relative_to(settings.MEDIA_ROOT) if absolute_name else self.test_file)
    # self.rel_url = reverse('get_protected_media', args=[self.rel_path])
    self.rel_url = reverse('get_protected_media', args=[urllib.parse.quote(str(self.test_file))])
    self.abs_url = get_test_absolute_url(self.rel_url)

  def tearDown(self):
    # manage differently with storage shutil.rmtree(self.test_file.parents[0])
    self.storage.delete(self.test_file)
    storage_rmtree(self.storage, self.test_file.parents[0])
    super().tearDown()

  def test_authenticated_user_can_access_protected_media(self):
    """test authenticated user can access protected media. This runs as a MemberTestCase so the user is logged in."""
    response = self.client.get(self.rel_url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertIsInstance(response, StreamingHttpResponse)
    # get the content of the response
    chunks = []
    for chunk in response.streaming_content:
      # chunk peut être bytes ou memoryview
      chunks.append(bytes(chunk))
    received = b"".join(chunks)
    # check the content of the response is the content of the file
    self.assertEqual(received, self.uploaded_content)
    self.assertTrue(response["Content-Type"].startswith("image/"))

  def test_unauthenticated_user_cannot_access_protected_media(self):
    """test non-authenticated user cannot access protected media. 
    This runs as a MemberTestCase so the first action os to logout."""
    self.client.logout()
    response = self.client.get(self.rel_url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'members/login/login.html')
    # print("request:", response.request)
    self.assertEqual(response.request['PATH_INFO'], reverse('members:login'))
    quoted_url = urllib.parse.quote(self.rel_url, safe='')
    self.assertEqual(response.request['QUERY_STRING'], f'next={quoted_url}')
