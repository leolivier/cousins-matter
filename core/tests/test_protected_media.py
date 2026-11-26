from pathlib import Path

import urllib.parse

from django.conf import settings
from django.urls import reverse
from django.http import StreamingHttpResponse

from django.core.files.storage import default_storage

from core.context_processors import override_settings
from core.utils import (
  test_resource_full_path,
  get_test_absolute_url,
  protected_media_url,
)
from members.tests.tests_member_base import MemberTestCase
from core.utils import storage_rmtree, test_media_root_decorator


class TestMediaResourceMixin:
  def copy_test_resource(self, resource_file, target_file, return_content=False):
    self.storage = default_storage
    # Copy the test resource
    with open(resource_file, "rb") as initial_file:
      real_name = self.storage.save(target_file, initial_file)
    if return_content:
      with open(resource_file, "rb") as initial_file:  # reopen as save above closes the file
        return (real_name, initial_file.read())
    else:
      return real_name

  def clean_storage(self, test_file):
    self.storage.delete(test_file)
    storage_rmtree(self.storage, Path(test_file).parents[0])


@test_media_root_decorator(__file__)
class ProtectedMediaTestCase(TestMediaResourceMixin, MemberTestCase):
  def setUp(self):
    super().setUp()
    # use test logo from resources as an image file to test the protected media
    # so copy it to /media/<tenant slug>/testdir/testimage.png
    self.test_file = Path(self.member.tenant.slug) / "test_protected_media" / "test_image.jpg"
    logo_file = test_resource_full_path("test-logo.jpg", __file__)
    (self.test_file, self.uploaded_content) = self.copy_test_resource(logo_file, self.test_file, return_content=True)
    self.rel_url = protected_media_url(self.test_file)
    self.abs_url = get_test_absolute_url(self.rel_url)

  def tearDown(self):
    self.clean_storage(self.test_file)
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
    self.assertTemplateUsed(response, "members/login/login.html")
    # print("request:", response.request)
    self.assertEqual(response.request["PATH_INFO"], reverse("members:login"))
    quoted_url = urllib.parse.quote(self.rel_url, safe="")
    self.assertEqual(response.request["QUERY_STRING"], f"next={quoted_url}")

  def _copy_foreign_file(self, path):
    logo_file = test_resource_full_path("test-logo.jpg", __file__)
    return self.copy_test_resource(logo_file, path)

  @override_settings(MULTI_TENANT_ENABLED=True)
  def test_member_cannot_read_another_tenants_media(self):
    foreign = self._copy_foreign_file(Path("other-tenant") / "test_protected_media" / "foreign.jpg")
    try:
      response = self.client.get(protected_media_url(foreign), follow=True)
      self.assertEqual(response.status_code, 404)
    finally:
      self.clean_storage(foreign)

  @override_settings(MULTI_TENANT_ENABLED=True)
  def test_superuser_can_read_another_tenants_media(self):
    foreign = self._copy_foreign_file(Path("other-tenant") / "test_protected_media" / "foreign.jpg")
    try:
      self.client.logout()
      self.assertTrue(self.client.login(username=self.superuser.email, password=self.superuser.password))
      response = self.client.get(protected_media_url(foreign))
      self.assertEqual(response.status_code, 200)
    finally:
      self.clean_storage(foreign)

  @override_settings(MULTI_TENANT_ENABLED=True)
  def test_legacy_unprefixed_path_is_404(self):
    legacy = self._copy_foreign_file(Path("legacy_media") / "x.jpg")
    try:
      response = self.client.get(protected_media_url(legacy))
      self.assertEqual(response.status_code, 404)
    finally:
      self.clean_storage(legacy)

  def test_protected_media_is_not_cacheable_by_shared_caches(self):
    """Protected media must stay out of shared caches (Cloudflare, proxies): only the browser caches it."""
    response = self.client.get(self.rel_url)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response["Cache-Control"], "private, max-age=3600")

  def test_etag_is_quoted_and_conditional_request_returns_304(self):
    """ETags must be quoted (RFC 7232) and a matching If-None-Match must answer 304 without reopening the file."""
    response = self.client.get(self.rel_url)
    etag = response["ETag"]
    self.assertTrue(etag.startswith('"') and etag.endswith('"'))
    not_modified = self.client.get(self.rel_url, HTTP_IF_NONE_MATCH=etag)
    self.assertEqual(not_modified.status_code, 304)
    self.assertEqual(not_modified["ETag"], etag)
    self.assertEqual(not_modified["Cache-Control"], "private, max-age=3600")


class PublicMediaCacheControlTestCase(TestMediaResourceMixin, MemberTestCase):
  def setUp(self):
    super().setUp()
    self.test_file = Path("public") / "test_public_media" / "test_image.jpg"
    logo_file = test_resource_full_path("test-logo.jpg", __file__)
    (self.test_file, self.uploaded_content) = self.copy_test_resource(logo_file, self.test_file, return_content=True)
    self.rel_url = f"{settings.PUBLIC_MEDIA_URL}test_public_media/test_image.jpg"

  def tearDown(self):
    self.clean_storage(self.test_file)
    super().tearDown()

  def test_public_media_is_cacheable_at_the_edge(self):
    """Public media is anonymous and identical for every visitor, so the CDN/browser may cache it."""
    response = self.client.get(self.rel_url)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response["Cache-Control"], "public, max-age=86400")
