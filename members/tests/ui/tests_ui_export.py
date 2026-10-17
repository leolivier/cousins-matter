from .base import MembersUITestBase


class ExportMembersUITest(MembersUITestBase):
  """UI tests for the export members page filter dropdowns."""

  def test_export_name_filter_selects_member(self):
    """Typing at least 2 chars shows options; clicking one fills the hidden input."""
    self.login_and_goto_page("members:select_members_to_export")

    search = self.page.locator("#name-id-dropdown input[type=search]")
    search.fill("Du")
    search.press("Enter")

    options = self.page.locator("#name-id-results .dropdown-item")
    options.first.wait_for(state="visible")
    self.assertGreaterEqual(options.count(), 1, "Dropdown should show matching options")

    self.page.locator("#name-id-results .dropdown-item", has_text="Dupont").click()

    self.assertEqual(self.page.locator("#name-id").input_value(), "Dupont")
