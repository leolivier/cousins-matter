from unittest.mock import patch, MagicMock
from urllib.error import HTTPError

from django.conf import settings

from members.tests.tests_member_base import MemberTestCase
from core.views.views_stats import get_github_release_version, get_latest_release_text


class TestGetGithubReleaseVersion(MemberTestCase):
  """Tests for get_github_release_version edge cases."""

  def _make_request(self):
    """Helper to get a request object via the test client."""
    from django.test import RequestFactory

    return RequestFactory().get("/dummy")

  @patch("core.views.views_stats.urlopen")
  def test_version_not_found(self, mock_urlopen):
    """Test that a missing tag_name returns None and sets error message."""
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"name": "some-release"}'
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_response

    request = self._make_request()
    request.user = self.member
    # Add message middleware support
    from django.contrib.messages.storage.fallback import FallbackStorage

    setattr(request, "session", "session")
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)

    result = get_github_release_version(request, "owner", "repo")
    self.assertIsNone(result)

  @patch("core.views.views_stats.urlopen")
  def test_http_error(self, mock_urlopen):
    """Test that an HTTPError returns None and sets error message."""
    mock_urlopen.side_effect = HTTPError(url="http://example.com", code=404, msg="Not Found", hdrs={}, fp=None)

    request = self._make_request()
    request.user = self.member
    from django.contrib.messages.storage.fallback import FallbackStorage

    setattr(request, "session", "session")
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)

    result = get_github_release_version(request, "owner", "repo")
    self.assertIsNone(result)


class TestGetLatestReleaseText(MemberTestCase):
  """Tests for get_latest_release_text version comparison logic."""

  def _make_request(self, user=None):
    from django.test import RequestFactory

    request = RequestFactory().get("/dummy")
    request.user = user or self.member
    from django.contrib.messages.storage.fallback import FallbackStorage

    setattr(request, "session", "session")
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)
    return request

  @patch("core.views.views_stats.get_github_release_version")
  def test_version_up_to_date(self, mock_get_version):
    """Test when current version equals latest release."""
    mock_get_version.return_value = settings.APP_VERSION
    request = self._make_request()
    result = get_latest_release_text(request)
    self.assertEqual(result["value"], settings.APP_VERSION)
    self.assertIn("info", result)
    self.assertEqual(result["icon"], "cool")

  @patch("core.views.views_stats.get_github_release_version")
  def test_version_newer_than_release(self, mock_get_version):
    """Test when current version is newer than latest release."""
    mock_get_version.return_value = "v0.0.1"
    request = self._make_request()
    result = get_latest_release_text(request)
    self.assertEqual(result["value"], "v0.0.1")
    self.assertIn("warning", result)
    self.assertEqual(result["icon"], "confused")

  @patch("core.views.views_stats.get_github_release_version")
  def test_version_outdated_superuser(self, mock_get_version):
    """Test outdated version warning with extra text for superuser."""
    mock_get_version.return_value = "v99.99.99"
    request = self._make_request(user=self.superuser)
    result = get_latest_release_text(request)
    self.assertEqual(result["value"], "v99.99.99")
    self.assertIn("warning", result)
    self.assertEqual(result["icon"], "poop")
    # Superuser gets additional update documentation text
    self.assertIn("<br>", result["warning"])

  @patch("core.views.views_stats.get_github_release_version")
  def test_version_outdated_non_superuser(self, mock_get_version):
    """Test outdated version warning without extra text for regular user."""
    mock_get_version.return_value = "v99.99.99"
    request = self._make_request(user=self.member)
    result = get_latest_release_text(request)
    self.assertIn("warning", result)
    self.assertNotIn("<br>", result["warning"])

  @patch("core.views.views_stats.get_github_release_version")
  def test_version_not_found(self, mock_get_version):
    """Test when GitHub version lookup fails."""
    mock_get_version.return_value = None
    request = self._make_request()
    result = get_latest_release_text(request)
    self.assertEqual(result["value"], "?")
    self.assertIn("error", result)
