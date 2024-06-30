from .tests_member_base import MemberTestCase


class LoginTests(MemberTestCase):

  def test_login_view(self):
    self.client.logout()  # make sure nobodys logged in
    self.assertMemberExists()
    response = self.client.get(self.login_url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'members/login/login.html')
    response = self.client.post(self.login_url, {'username': self.username, 'password': self.password}, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertMemberIsLogged()


class PasswordTests(MemberTestCase):

  def test_change_password_view(self):
    response = self.client.get(self.change_password_url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'members/login/password_change.html')
    newpass = self.password+'1'

    # check password change
    response = self.client.post(self.change_password_url,
                                {'old_password': self.password, 'password1': newpass, 'password2': newpass}, follow=True)

    # self.assertRedirects(response, self.login_url, 200)
    self.assertEqual(response.status_code, 200)
    self.assertMemberIsLogged()
