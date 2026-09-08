import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from unittest.mock import patch

from django.urls import reverse

from . import PlaywrightTestCase

# stubbed probe results: keeps the UI suite fast and independent of Redis/S3/qcluster
_STUB_CHECKS = [
  {"name": "Database", "status": "ok", "label": "ok", "detail": "stub detail", "long_output": False},
  {"name": "Redis", "status": "ok", "label": "ok", "detail": "stub detail", "long_output": False},
]


class EnvCheckUITests(PlaywrightTestCase):
  """UI tests for the environment check page (superuser only)."""

  def test_env_check_requires_login(self):
    """Anonymous visitors are redirected to the login page."""
    self.page.goto(self.url(reverse("core:env_check")))
    self.assert_url_contains("/login")

  def test_env_check_page_and_navbar_link_are_visible(self):
    # patch the name the view uses (direct import), not core.services
    with patch("core.views.views_stats.run_env_checks", return_value=_STUB_CHECKS):
      self.login_and_goto_page("core:env_check")
    self.assert_visible("h1.title")
    self.assert_visible("table.table")
    self.assert_visible("tr:has-text('Database')")
    # the navbar link lives inside Bulma's (closed) settings dropdown: assert presence
    self.assertEqual(self.page.locator(f"a[href='{reverse('core:env_check')}']").count(), 1)
