from django.test import TestCase
from django.urls import reverse
from pprint import pprint
from django.utils.translation import gettext as _
from django.contrib.auth.models import User

TEST_USER={'username': 'foobar', 'password': 'vWx12/gtV"',  "email": "foo@bar.com",
					 "first_name": "foo", "last_name": "bar" }

def sreverse(url):
	return reverse(url).rstrip('/')

   
class LoginRequiredTests(TestCase):
	def test_login_required(self):
		for url in ['accounts:logout', 'accounts:change_password']:
			response = self.client.get(reverse(url))
			# checks that the response is a redirect (302) to the login page 
			# with another redirect afterwaud to the original url
			self.assertRedirects(response, f"{sreverse('accounts:login')}?next={reverse(url)}", 302, 301)

class RegisterTests(TestCase):

	def test_register_view(self):
		user = {}
		response = self.client.get(reverse('accounts:register'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'accounts/register.html')
		user['username'] = 'foobar1'
		user['password1'] = "<PASSWORD>"
		user['password2'] = "<PASSWORD>"
		response = self.client.post(reverse('accounts:register'), user)
		self.assertContains(response, _("This password is too common."))
		user['password1'] = user['password2'] = 'vWx12/gtV"'
		response = self.client.post(reverse('accounts:register'), user) 
		self.assertContains(response, _("This field is required."))
		user['email'] = "foo@bar1.com"
		response = self.client.post(reverse('accounts:register'), user)
		self.assertContains(response, _("This field is required."))
		user['first_name'] = 'foo'
		response = self.client.post(reverse('accounts:register'), user)
		self.assertContains(response, _("This field is required."))
		user['last_name'] = 'bar1'
		response = self.client.post(reverse('accounts:register'), user) 
		self.assertRedirects(response, reverse('accounts:login'), 302, 200)
		user = User.objects.filter(username=user['username'])
		self.assertTrue(user.exists())

class PasswordTests(TestCase):
	def setUp(self):
		self.user = User.objects.create(**TEST_USER)
		self.assertTrue(User.objects.filter(username=self.user.username).exists())
		self.credentials = {'username': self.user.username, 'password': self.user.password}
		self.newpass = f'{self.user.password}+1'

	def test_login_view(self):
		response = self.client.get(reverse('accounts:login'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'accounts/login.html')
		response = self.client.post(sreverse('accounts:login'), {'username': 'what', 'password': 'is this?'}, follow=True)
		self.assertEqual(response.status_code, 200)
		pprint(vars(response.context['messages']))
		self.assertTrue(response.context['user'].is_authenticated)

	def test_change_password_view(self):
		response = self.client.post(reverse('accounts:login'), self.credentials, follow=True)
		self.assertEqual(response.status_code, 200)
		response = self.client.get(reverse('accounts:change_password'))
		# pprint(vars(response))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'accounts/password_change.html')
		response = self.client.post(reverse('accounts:change_password'), {'password1': self.user.password, 'password2': self.newpass})
		self.assertContains(response, _("The two password fields didn’t match."))
		response = self.client.post(reverse('accounts:change_password'), {'password1': self.newpass, 'password2': self.newpass})
		self.assertRedirects(response, reverse('accounts:login'), 302, 200)
