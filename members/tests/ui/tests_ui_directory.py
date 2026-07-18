from .base import MembersUITestBase


class DirectoryUITest(MembersUITestBase):
  """UI tests for the members directory page."""

  def test_directory_display(self):
    """The directory should display a table of members."""
    self.login_and_goto_page("members:directory")

    self.assert_visible("h1.title", "Directory title should be visible")

    # Table should be visible
    self.assert_visible("table.table", "Members directory table should be visible")

    # At least one row (excluding header)
    rows = self.page.locator("table.table tr")
    # Header row + at least the admin user
    self.assertGreaterEqual(rows.count(), 2, "Table should have header row and at least one member row")

    # Print button (uses data-print-section, delegated in core.js)
    print_btn = self.page.locator("button[data-print-section]")
    self.assertTrue(print_btn.is_visible(), "Print button should be visible")

  def test_directory_pdf_link(self):
    """The directory page should have a PDF export link."""
    self.login_and_goto_page("members:directory")

    pdf_link = self.page.locator("a[href*='directory/print']")
    self.assertTrue(pdf_link.is_visible(), "PDF export link should be visible")


class BirthdaysUITest(MembersUITestBase):
  """UI tests for the birthdays page."""

  def test_birthdays_display(self):
    """The birthdays page should be accessible and show content."""
    self.login_and_goto_page("members:birthdays")

    # The birthdays page should display something meaningful
    # Either a title with the ndays count, or a "no birthdays" message
    content = self.page.content()
    has_content = "Birthdays" in content or "birthdays" in content or "No birthdays" in content or "anniversaire" in content
    self.assertTrue(
      has_content,
      f"Birthdays page should show content, got title: {self.page.evaluate('document.title')}",
    )
