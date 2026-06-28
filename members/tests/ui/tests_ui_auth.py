
from .base import MembersUITestBase


class AuthUITest(MembersUITestBase):
  """UI tests for authentication pages."""

  def test_login_page_display(self):
    """The login page should display the sign-in form."""
    self.goto_page("members:login")

    self.assert_visible("h1.title, legend.title", "Login page title should be visible")
    self.assert_visible("input[name='username']", "Username field should be visible")
    self.assert_visible("input[name='password']", "Password field should be visible")
    self.assert_visible("button[type='submit']", "Sign-in button should be visible")

  def test_login_success(self):
    """Login with valid credentials should succeed and show the navbar."""
    self.login("admin", "password")
    self.assert_visible("nav.navbar", "Navbar should be visible after login")
    self.assertNotIn("/login/", self.page.url, "Should not be on login page after login")

  def test_members_page_requires_auth(self):
    """The members list page should redirect to login when not authenticated."""
    self.goto_page("members:members")
    self.assertIn("/login/", self.page.url, "Unauthenticated user should be redirected to login")

  def test_member_detail_requires_auth(self):
    """The member detail page should redirect to login when not authenticated."""
    self.goto_page("members:detail", kwargs={"username": self.member1.username})
    self.assertIn("/login/", self.page.url, "Unauthenticated user should be redirected to login")

  def test_profile_requires_auth(self):
    """The profile edit page should redirect to login when not authenticated."""
    self.goto_page("members:profile")
    self.assertIn("/login/", self.page.url, "Unauthenticated user should be redirected to login")

  def test_directory_requires_auth(self):
    """The directory page should redirect to login when not authenticated."""
    self.goto_page("members:directory")
    self.assertIn("/login/", self.page.url, "Unauthenticated user should be redirected to login")
