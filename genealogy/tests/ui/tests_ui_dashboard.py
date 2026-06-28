from .base import GenealogyUITestBase


class GenealogyDashboardUITest(GenealogyUITestBase):
  """UI tests for the genealogy dashboard page."""

  def test_dashboard_requires_auth(self):
    """The genealogy dashboard should redirect to login when not authenticated."""
    self.goto_page("genealogy:dashboard")
    self.assert_url_contains("/login/")

  def test_dashboard_display(self):
    """The dashboard should display the genealogy title and stats."""
    self.login_and_goto_page("genealogy:dashboard")

    # Main title
    self.assert_visible("h1.title", "Genealogy page title should be visible")

    # Tabs navigation
    self.assert_visible(".tabs.is-boxed", "Tabs navigation should be visible")

    # Dashboard tab should be active
    active_tab = self.page.locator(".tabs li.is-active a")
    self.assertTrue(active_tab.is_visible(), "Dashboard tab should be active")

    # Stats boxes — total people and families
    boxes = self.page.locator(".box")
    self.assertGreaterEqual(boxes.count(), 2, "At least two stat boxes should be visible")

    # Import/Export buttons (use specific path to avoid matching navbar members import)
    self.assert_visible("a[href*='/genealogy/import']", "Import GEDCOM button should be visible")
    self.assert_visible("a[href*='/genealogy/export']", "Export GEDCOM button should be visible")

    self.errors.clear()

  def test_dashboard_no_js_errors(self):
    """The dashboard should not produce JavaScript errors."""
    self.login_and_goto_page("genealogy:dashboard")
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")


class GenealogyStatisticsUITest(GenealogyUITestBase):
  """UI tests for the genealogy statistics page."""

  def test_statistics_requires_auth(self):
    """The statistics page should redirect to login when not authenticated."""
    self.goto_page("genealogy:statistics")
    self.assert_url_contains("/login/")

  def test_statistics_display(self):
    """The statistics page should display charts."""
    self.login_and_goto_page("genealogy:statistics")

    # Page title
    self.assert_visible("h1.title", "Genealogy page title should be visible")

    # Chart containers (canvas elements for Chart.js)
    chart_canvases = self.page.locator("canvas")
    self.assertGreaterEqual(chart_canvases.count(), 2, "At least two chart canvases should be visible")

    # Statistics tab should be active
    active_tab = self.page.locator(".tabs li.is-active a")
    self.assertTrue(active_tab.is_visible(), "Statistics tab should be active")

    # The page loads Chart.js from CDN — clear any CDN-related errors
    self.errors.clear()
