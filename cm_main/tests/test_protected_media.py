import shutil
import urllib.parse
from django.conf import settings
from django.urls import reverse
from django.http import StreamingHttpResponse

from cm_main.utils import test_resource_full_path, get_test_absolute_url
from members.tests.tests_member_base import MemberTestCase


class ProtectedMediaTestCase(MemberTestCase):
  def setUp(self):
    super().setUp()
    # use test logo from resources as an image file to test the protected media
    # so copy it to /media/testdir/testimage.png
    self.test_file = settings.MEDIA_ROOT / 'test_protected_media' / 'test_image.jpg'
    logo_file = test_resource_full_path('test-logo.jpg', __file__)
    # Make sure the destination directory exists
    self.test_file.parent.mkdir()
    # Copy the test resource
    shutil.copy2(logo_file, self.test_file)
    self.rel_path = str(self.test_file.relative_to(settings.MEDIA_ROOT))
    self.rel_url = reverse('get_protected_media', args=[self.rel_path])
    self.abs_url = get_test_absolute_url(self.rel_url)

  def tearDown(self):
    shutil.rmtree(self.test_file.parents[0])
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
    expected = self.test_file.read_bytes()
    self.assertEqual(received, expected)
    self.assertTrue(response["Content-Type"].startswith("image/"))

  def test_unauthenticated_user_cannot_access_protected_media(self):
    """test non-authenticated user cannot access protected media. 
    This runs as a MemberTestCase so the first action os to logout."""
    self.client.logout()
    response = self.client.get(self.rel_url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'members/login/login.html')
    print("request:", response.request)
    self.assertEqual(response.request['PATH_INFO'], reverse('members:login'))
    quoted_url = urllib.parse.quote(self.rel_url, safe='')
    self.assertEqual(response.request['QUERY_STRING'], f'next={quoted_url}')
