from django.utils.translation import gettext as _

from ..models import Member
from .tests_member_base import MemberTestCase


class LoginTests(MemberTestCase):
  def test_login_view(self):
    """Tests the login view."""
    self.client.logout()  # make sure nobodys logged in
    self.assertMemberExists(self.member)
    response = self.client.get(self.login_url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "members/login/login.html")
    response = self.client.post(
      self.login_url, {"username": self.member.username, "password": self.member.password}, follow=True
    )
    self.assertEqual(response.status_code, 200)
    self.assertRequestUserIsLogged()

  def test_login_inactive_member(self):
    """An inactive member with correct credentials gets the 'not yet active' error."""
    self.client.logout()
    Member.objects.create_member(
      username="inactive_login",
      email="inactive_login@example.com",
      password=self.member.password,
      first_name="Inactive",
      last_name="Login",
      is_active=False,
      member_manager=self.superuser,
    )
    response = self.client.post(self.login_url, {"username": "inactive_login", "password": self.member.password}, follow=True)
    self.assertFormError(
      response.context["form"],
      None,
      [_("This account is not yet active. Please use the invitation link sent to you by email.")],
    )

  def test_login_inactive_member_wrong_password(self):
    """An inactive member with a wrong password still gets the generic error."""
    self.client.logout()
    Member.objects.create_member(
      username="inactive_login2",
      email="inactive_login2@example.com",
      password=self.member.password,
      first_name="Inactive",
      last_name="Login",
      is_active=False,
      member_manager=self.superuser,
    )
    response = self.client.post(
      self.login_url, {"username": "inactive_login2", "password": f"{self.member.password}wrong"}, follow=True
    )
    self.assertFormError(
      response.context["form"],
      None,
      [
        _("Please enter a correct %(username)s and password. Note that both fields may be case-sensitive.")
        % {"username": "username"}
      ],
    )

  def test_logout_view(self):
    """Tests the logout view."""
    self.client.login(username=self.member.username, password=self.member.password)
    response = self.client.get(self.logout_url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertFalse(self.current_user().is_authenticated)
    self.assertTemplateUsed(response, "members/login/login.html")


class PasswordTests(MemberTestCase):
  def test_change_password_view(self):
    """Tests the change password view."""
    response = self.client.get(self.change_password_url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "members/login/password_change.html")
    # check password change
    response = self.client.post(
      self.change_password_url,
      {"old_password": self.member.password, "password1": f"{self.member.password}1", "password2": f"{self.member.password}1"},
      follow=True,
    )

    # self.assertRedirects(response, self.login_url, 200)
    self.assertEqual(response.status_code, 200)
    self.assertRequestUserIsLogged()
