import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from .base import SaasUITestBase


class LandingUITest(SaasUITestBase):
  """The SaaS landing page takes over the home for anonymous visitors."""

  def test_landing_page_anonymous(self):
    """Anonymous visitors see the landing: hero, signup CTA and 3 feature boxes."""
    self.goto_page("core:Home")
    self.assert_visible("section.hero p.title", "Landing hero title should be visible")
    self.assert_visible("section.hero a[href*='/saas/signup/']", "Signup CTA should be visible")
    self.assertEqual(self.page.locator(".box").count(), 3, "Landing should show 3 feature boxes")
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")

  def test_landing_hidden_when_authenticated(self):
    """Authenticated members get the regular app home, not the landing."""
    self.login_and_goto_page("core:Home")
    self.assert_hidden("section.hero.is-primary", "Landing hero should not be shown when authenticated")
    self.assert_visible("nav.navbar", "App navbar should be visible")
