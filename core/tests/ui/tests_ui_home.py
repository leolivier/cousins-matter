import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from . import PlaywrightTestCase


class HomeUITest(PlaywrightTestCase):
  """UI tests for the home page."""

  def test_home_page_loads_without_auth(self):
    """Home page should be accessible to unauthenticated visitors."""
    self.goto_page("core:Home")
    self.assert_visible("footer.footer", "Footer should be visible")
    # no JS errors
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")

  def test_home_page_has_htmx_loaded(self):
    """Home page should load htmx and essential scripts."""
    self.goto_page("core:Home")
    htmx_loaded = self.page.evaluate("() => typeof htmx !== 'undefined'")
    self.assertTrue(htmx_loaded, "htmx should be loaded on home page")

  def test_home_page_footer_links(self):
    """Footer should contain contact and about links."""
    self.goto_page("core:Home")
    footer = self.page.locator("footer.footer")
    self.assertTrue(footer.is_visible(), "Footer should be visible")
    # contact link
    contact_link = footer.locator("a[href*='contact']")
    self.assertTrue(contact_link.is_visible(), "Contact link should be visible in footer")

  def test_home_page_authenticated(self):
    """Home page should load correctly for authenticated users."""
    self.login_and_goto_page("core:Home")
    self.assert_visible("nav.navbar", "Navbar should be visible")
    self.assert_visible("footer.footer", "Footer should be visible for authenticated user")
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")

  def test_home_page_no_js_errors(self):
    """Home page should not trigger JS errors when navigating."""
    self.goto_page("core:Home")
    self.page.wait_for_timeout(1000)  # let JS settle
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")
