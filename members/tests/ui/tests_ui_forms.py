from .base import MembersUITestBase


class RegistrationUITest(MembersUITestBase):
  """UI tests for the registration request page."""

  def test_registration_request_form_display(self):
    """The registration request form should be accessible without auth."""
    self.goto_page("members:register_request")

    self.assert_visible("h1.title", "Registration request title should be visible")

    # Form fields
    self.assert_visible("input[name='name']", "Name field should be visible")
    self.assert_visible("input[name='email']", "Email field should be visible")
    self.assert_visible("textarea[name='message']", "Message textarea should be visible")

    # Submit button
    submit_btn = self.page.locator("button[type='submit']")
    self.assertTrue(submit_btn.is_visible(), "Submit button should be visible")


class ImportUITest(MembersUITestBase):
  """UI tests for the CSV import page (admin only)."""

  def test_import_members_form_display(self):
    """The CSV import form should be accessible to admin."""
    self.login_and_goto_page("members:csv_import")

    self.assert_visible("h1.title", "Import members title should be visible")

    # CSV file input
    self.assert_visible("input[name='csv_file']", "CSV file input should be visible")

    # Activate users checkbox
    self.assert_visible("input[name='activate_users']", "Activate users checkbox should be visible")

    # Import button
    import_btn = self.page.locator("button[type='submit']")
    self.assertTrue(import_btn.is_visible(), "Import button should be visible")
