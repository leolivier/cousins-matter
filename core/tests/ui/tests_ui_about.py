import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from . import PlaywrightTestCase


class AboutUITest(PlaywrightTestCase):
  """UI tests for the about / site statistics page."""

  def test_about_page_requires_auth(self):
    """About page should redirect to login when not authenticated."""
    self.goto_page("core:about")
    self.assertIn("/login/", self.page.url, "Unauthenticated user should be redirected to login")

  def test_about_page_display(self):
    """About page should show statistics sections for authenticated users."""
    self.login_and_goto_page("core:about")

    # page title
    self.assert_visible("h1.title", "Page title should be visible")

    # statistics panel
    self.assert_visible("section.panel", "Statistics panel should be visible")

    # category tabs
    tabs = self.page.locator(".stat-category")
    self.assertGreaterEqual(tabs.count(), 1, "At least one category tab should be visible")

    # at least one panel-category should be present
    panels = self.page.locator(".panel-category")
    self.assertGreaterEqual(panels.count(), 1, "At least one panel category should be visible")

  def test_about_page_tab_navigation(self):
    """Clicking a tab should show the corresponding category panel."""
    self.login_and_goto_page("core:about")

    # get all tab links
    tabs = self.page.locator(".stat-category")
    tab_count = tabs.count()

    if tab_count >= 2:
      # click the second tab
      second_tab = tabs.nth(1)
      second_category = second_tab.get_attribute("data-category")
      second_tab.scroll_into_view_if_needed()
      second_tab.click()
      self.page.wait_for_timeout(500)

      # the corresponding panel should exist
      panel = self.page.locator(f"#category-{second_category}")
      self.assertTrue(panel.is_visible(), f"Panel for '{second_category}' should be visible")

  def test_about_page_panel_blocks(self):
    """Each panel should contain stat blocks with key/value pairs."""
    self.login_and_goto_page("core:about")

    blocks = self.page.locator(".panel-block")
    self.assertGreaterEqual(blocks.count(), 1, "At least one stat block should be visible")

  def test_about_page_no_js_errors(self):
    """About page should not have JS errors."""
    self.login_and_goto_page("core:about")
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors on about page: {self.errors}")
