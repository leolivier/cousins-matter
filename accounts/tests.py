from django.test import TestCase
from django.urls import reverse
from pprint import pprint
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model

class TestObject:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
        
TEST_USER=TestObject(username='foobar', password='vWx12/gtV"',  email="foo@bar.com",
           					first_name="foo", last_name="bar")

def sreverse(url):
  return reverse(url).rstrip('/')

   
class LoginRequiredTests(TestCase):
  def test_login_required(self):
    for url in ['accounts:logout', 'accounts:change_password']:
      response = self.client.get(reverse(url))
      # checks that the response is a redirect (302) to the login page 
      # with another redirect afterwaud to the original url
      self.assertRedirects(response, f"{sreverse('accounts:login')}?next={reverse(url)}", 302, 301)

class PasswordTests(TestCase):
  def setUp(self):
    User = get_user_model()
    self.user = User.objects.create_user(TEST_USER.username, TEST_USER.email, TEST_USER.password)
    self.assertTrue(User.objects.filter(username=self.user.username).exists())
    
  def login(self):
    logged = self.client.login(username=TEST_USER.username, password=TEST_USER.password)
    self.assertTrue(logged)
      
  def test_login_view(self):
    response = self.client.get(reverse('accounts:login'))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'accounts/login.html')
    response = self.client.post(sreverse('accounts:login'), {'username': 'what', 'password': 'is this?'}, follow=True)
    self.assertEqual(response.status_code, 200)
		# TODO: how to check the user is authenticated?
    print("is authenticated:", response.context['user'].is_authenticated)
    # self.assertTrue(response.context['user'].is_authenticated)

  def test_change_password_view(self):
    self.login()
    response = self.client.get(reverse('accounts:change_password'))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'accounts/password_change.html')
    newpass=TEST_USER.password+'1'
    # TODO: how to check passwords match?
    # response = self.client.post(reverse('accounts:change_password'), {'old_password': TEST_USER.password, 'password1': TEST_USER.password, 'password2': newpass})
    # self.assertContains(response, _("The two password fields didn’t match."))
    response = self.client.post(reverse('accounts:change_password'), {'old_password': TEST_USER.password, 'password1': newpass, 'password2': newpass}, follow=True)
    pprint(vars(response))
    self.assertRedirects(response, reverse('accounts:login'), 200)
    self.assertTrue(self.client.login(username=TEST_USER.username, password=newpass))