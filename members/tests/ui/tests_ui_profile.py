from .base import MembersUITestBase


class ProfileUITest(MembersUITestBase):
  """UI tests for the profile edit page."""

  def test_profile_form_display(self):
    """The profile edit form should display all expected fields."""
    self.login_and_goto_page("members:profile")

    self.assert_visible("h1.title", "Profile form title should be visible")

    # Core fields
    self.assert_visible("input[name='username']", "Username field should be visible")
    self.assert_visible("input[name='email']", "Email field should be visible")
    self.assert_visible("input[name='first_name']", "First name field should be visible")
    self.assert_visible("input[name='last_name']", "Last name field should be visible")

    # Submit button
    self.assert_visible("button[type='submit']", "Submit button should be visible")

  def test_profile_form_has_change_password_link(self):
    """The profile page should have a link to change password."""
    self.login_and_goto_page("members:profile")

    password_link = self.page.locator("a[href*='password/change']")
    self.assertTrue(password_link.is_visible(), "Change password link should be visible")


class CreateMemberUITest(MembersUITestBase):
  """UI tests for the create member page (admin only)."""

  def test_create_member_form_display(self):
    """The create member form should display fields for admin users."""
    self.login_and_goto_page("members:create")

    self.assert_visible("h1.title", "Create member form title should be visible")

    # Core fields
    self.assert_visible("input[name='username']", "Username field should be visible")
    self.assert_visible("input[name='first_name']", "First name field should be visible")
    self.assert_visible("input[name='last_name']", "Last name field should be visible")

    # Submit button
    self.assert_visible("button[type='submit']", "Submit button should be visible")


class EditMemberUITest(MembersUITestBase):
  """UI tests for editing a member (admin)."""

  def test_edit_member_form_display(self):
    """Admin should be able to edit any member."""
    self.login_and_goto_page("members:member_edit", kwargs={"username": self.member1.username})

    self.assert_visible("h1.title", "Edit member form title should be visible")

    # Fields should be pre-filled with member data
    self.assert_visible("input[name='username']", "Username field should be visible")
    self.assert_visible("input[name='first_name']", "First name field should be visible")

    # Delete button should be visible for admin
    delete_btn = self.page.locator("button.is-warning")
    self.assertTrue(delete_btn.is_visible(), "Delete button should be visible for admin")
