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
      self.login_url,
      {"username": self.member.username, "password": self.member.password},
      follow=True,
    )
    self.assertEqual(response.status_code, 200)
    self.assertRequestUserIsLogged()

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
    newpass = self.member.password + "1"

    # check password change
    response = self.client.post(
      self.change_password_url,
      {
        "old_password": self.member.password,
        "password1": newpass,
        "password2": newpass,
      },
      follow=True,
    )

    # self.assertRedirects(response, self.login_url, 200)
    self.assertEqual(response.status_code, 200)
    self.assertRequestUserIsLogged()
