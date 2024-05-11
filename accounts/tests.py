from django.test import SimpleTestCase
from django.urls import reverse
from django.contrib.auth import get_user
from django.contrib.auth.models import User


def sreverse(url):
  return reverse(url).rstrip('/')


class AccountTestCase(SimpleTestCase):
  databases = '__all__'  # allow write to database

  account = None
  username = 'foobar'
  password = 'vWx12/gtV"'
  email = "foo@bar.com"
  first_name = "foo"
  last_name = "bar"

  superuser = None
  superuser_name = "superuser"
  superuser_pwd = "SuPerUser1!"
  superuser_email = "superuser@test.com"

  login_url = reverse('accounts:login')
  logout_url = reverse('accounts:logout')
  change_password_url = reverse('change_password')

  def setUp(self):
    super().setUp()
    if not self.superuser:
      self.superuser = User.objects.filter(username=self.superuser_name).first()
      if not self.superuser:
        self.superuser = User.objects.create_superuser(self.superuser_name, self.superuser_email, self.superuser_pwd)

  def next(self, from_url, to_url):
    return f"{from_url}?next={to_url}"

  def get_or_create_account(self):
    if self.account is None:
      faccount = User.objects.filter(username=self.username)
      if faccount.exists():
        self.account = faccount.first()
      else:
        self.account = User.objects.create_user(self.username, self.email, self.password,
                                                first_name=self.first_name, last_name=self.last_name, is_active=True)
    return self.account

  def delete_account(self):
    self.account.delete()

  def login(self):
    self.assertAccountExists()
    user = get_user(self.client)
    logged = user.is_authenticated or self.client.login(username=self.username, password=self.password)
    self.assertTrue(logged)

  def assertAccountExists(self):
    self.assertTrue(User.objects.filter(username=self.username).exists())

  def assertAccountIsLogged(self):
    user = get_user(self.client)
    self.assertTrue(user.is_authenticated)

  def assertAccountIsNotLogged(self):
    user = get_user(self.client)
    self.assertFalse(user.is_authenticated)

  def superuser_login(self):
    self.assertIsNotNone(self.superuser)
    user = get_user(self.client)
    if user.is_authenticated and not user.is_superuser:
      self.client.logout()
      user = get_user(self.client)  # is refresh needed?
    logged = user.is_authenticated or self.client.login(username=self.superuser_name, password=self.superuser_pwd)
    self.assertTrue(logged)


class CreatedAccountTestCase(AccountTestCase):
  def setUp(self) -> None:
    super().setUp()
    self.get_or_create_account()

  # def tearDown(self) -> None:
  #   self.delete_account()
  #   return super().tearDown()


class LoggedAccountTestCase(CreatedAccountTestCase):
  def setUp(self):
    super().setUp()
    self.login()


class LoginRequiredTests(AccountTestCase):
  def test_login_required(self):
    response = self.client.get(self.logout_url)
    self.assertRedirects(response, self.next(self.login_url, self.logout_url), 302, 200)
    response = self.client.get(self.change_password_url)
    self.assertRedirects(response, self.next(self.login_url, self.change_password_url), 302, 200)


class LoginTests(CreatedAccountTestCase):

  def test_login_view(self):
    self.assertAccountExists()
    response = self.client.get(self.login_url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'accounts/login.html')
    response = self.client.post(self.login_url, {'username': self.username, 'password': self.password}, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertAccountIsLogged()


class PasswordTests(LoggedAccountTestCase):

  def test_change_password_view(self):
    response = self.client.get(self.change_password_url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'accounts/password_change.html')
    newpass = self.password+'1'

    # check password change
    response = self.client.post(self.change_password_url,
                                {'old_password': self.password, 'password1': newpass, 'password2': newpass}, follow=True)

    # self.assertRedirects(response, self.login_url, 200)
    self.assertEqual(response.status_code, 200)
    self.assertAccountIsLogged()
