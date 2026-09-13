from django.http import Http404
from django.test import RequestFactory

from members.tests.tests_member_base import MemberTestCase
from ..models import create_page
from ..views import flatpage
from .test_base import BasePageTestCase


class TestFlatpageRedirect(BasePageTestCase, MemberTestCase):
  def test_append_slash_redirect_stays_on_site(self):
    create_page("/foo/", "a title", "a content")
    response = self.client.get("/pages/foo")
    self.assertRedirects(response, "/pages/foo/", status_code=301, target_status_code=200)

  def _request_with_raw_path(self, path):
    # the test client parses "//host/..." as a URL (netloc stripped), so craft
    # the request as TenantFlatpageFallbackMiddleware does: flatpage(request, request.path)
    request = RequestFactory().get("/")
    request.path = path
    return request

  def test_protocol_relative_url_is_not_redirected(self):
    # planted page (the model has no url validator): a 301 to "//evil.com/x/"
    # would send browsers to an external site (CWE-601)
    create_page("//evil.com/x/", "a title", "a content")
    request = self._request_with_raw_path("//evil.com/x")
    with self.assertRaises(Http404):
      flatpage(request, request.path)

  def test_backslash_url_is_not_redirected(self):
    # browsers normalize "\" to "/", so "/\evil.com/x/" is protocol-relative too
    create_page("/\\evil.com/x/", "a title", "a content")
    request = self._request_with_raw_path("/\\evil.com/x")
    with self.assertRaises(Http404):
      flatpage(request, request.path)
