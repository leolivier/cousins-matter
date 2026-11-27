from pathlib import Path

import urllib.parse
from unittest.mock import patch

from django.conf import settings
from django.urls import reverse
from django.http import StreamingHttpResponse
from django.test import SimpleTestCase

from django.core.files.storage import default_storage

from core.context_processors import override_settings
from core.views import views_general
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

  def test_remote_backend_redirects_to_the_signed_url(self):
    signed = "https://bucket.example/acme/test.jpg?sig=1"
    with (
      patch("core.views.views_general._direct_media_url", return_value=signed),
      patch("core.views.views_general.default_storage") as storage,
    ):
      storage.exists.return_value = True
      response = self.client.get(self.rel_url)
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response["Location"], signed)
    self.assertEqual(response["Cache-Control"], "private, max-age=300")

  def test_remote_backend_missing_file_is_404(self):
    # A signed URL is issued for any key, so the view checks the object first
    # instead of sending the browser to the bucket's XML 404.
    with (
      patch("core.views.views_general._direct_media_url", return_value="https://bucket.example/x.jpg"),
      patch("core.views.views_general.default_storage") as storage,
    ):
      storage.exists.return_value = False
      response = self.client.get(self.rel_url)
    self.assertEqual(response.status_code, 404)

  def tearDown(self):
    self.clean_storage(self.test_file)
    super().tearDown()

  def test_authenticated_user_can_access_protected_media(self):
    """test authenticated user can access protected media. This runs as a MemberTestCase so the user is logged in."""
    # Force the streaming branch so the content check runs on any backend
    # (CI stores media in S3, where the view redirects instead).
    with patch("core.views.views_general._direct_media_url", return_value=None):
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
      with patch("core.views.views_general._direct_media_url", return_value=None):
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
    # Force the streaming branch: CI stores media in S3, where the view redirects.
    with patch("core.views.views_general._direct_media_url", return_value=None):
      response = self.client.get(self.rel_url)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response["Cache-Control"], "private, max-age=3600")

  def test_etag_is_quoted_and_conditional_request_returns_304(self):
    """ETags must be quoted (RFC 7232) and a matching If-None-Match must answer 304 without reopening the file."""
    with patch("core.views.views_general._direct_media_url", return_value=None):
      response = self.client.get(self.rel_url)
      etag = response["ETag"]
      self.assertTrue(etag.startswith('"') and etag.endswith('"'))
      not_modified = self.client.get(self.rel_url, HTTP_IF_NONE_MATCH=etag)
    self.assertEqual(not_modified.status_code, 304)
    self.assertEqual(not_modified["ETag"], etag)
    self.assertEqual(not_modified["Cache-Control"], "private, max-age=3600")

  def test_non_ascii_filename_is_served(self):
    """Accented names must be encoded exactly once (é -> %C3%A9, never %25C3%25A9).

    ``protected_media_url`` used to ``quote()`` the name before ``reverse()``,
    which encoded it again: every media with a non-ASCII name 404'd.
    """
    target = Path(self.member.tenant.slug) / "test_protected_media" / "américains_Littry.png"
    logo_file = test_resource_full_path("test-logo.jpg", __file__)
    self.copy_test_resource(logo_file, target)

    url = protected_media_url(target)

    self.assertNotIn("%25", url)
    # Force the streaming branch: CI stores media in S3, where the view redirects.
    with patch("core.views.views_general._direct_media_url", return_value=None):
      response = self.client.get(url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertIsInstance(response, StreamingHttpResponse)


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
    with patch("core.views.views_general._direct_media_url", return_value=None):
      response = self.client.get(self.rel_url)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response["Cache-Control"], "public, max-age=86400")


class DirectMediaUrlTests(SimpleTestCase):
  """Only a backend URL that this view does not itself serve is followed."""

  def test_url_served_by_this_view_is_not_followed(self):
    with patch("core.views.views_general.default_storage") as storage:
      storage.url.return_value = f"{settings.MEDIA_URL}acme/file.jpg"
      self.assertIsNone(views_general._direct_media_url("acme/file.jpg"))

  def test_remote_backend_url_is_returned(self):
    with patch("core.views.views_general.default_storage") as storage:
      storage.url.return_value = "https://bucket.example/acme/file.jpg?sig=1"
      self.assertEqual(views_general._direct_media_url("acme/file.jpg"), storage.url.return_value)

  def test_signing_failure_falls_back_to_streaming(self):
    with patch("core.views.views_general.default_storage") as storage:
      storage.url.side_effect = ValueError("unsafe name")
      self.assertIsNone(views_general._direct_media_url("../../etc/passwd"))
