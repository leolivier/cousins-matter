from datetime import date
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.urls import reverse
from django.core import mail
from django.utils.translation import gettext as _
from django.conf import settings
from django.test import SimpleTestCase, RequestFactory
from pprint import pprint

from members.registration_link_manager import RegistrationLinkManager

from ..models import Member
from .tests_member import MemberTestCase
from accounts.tests import AccountTestCase

class MemberInviteTests(MemberTestCase):

	def do_test_invite(self, sender):
		test_invite = { 'invited': "Mr Freeze", 'email': 'test-cousinsmatter@maildrop.cc'}
		response  = self.client.post(reverse("members:invite"), test_invite, follow=True)
		# pprint(vars(response))
		self.assertContains(response, 
											f'''<div class="message-body">{_("Invitation sent to {email}.").format(email=test_invite['email'])}</div>''', 
											html=True)
		self.assertEqual(len(mail.outbox), 1)
		self.assertSequenceEqual(mail.outbox[0].recipients(), [test_invite['email']])
		self.assertEqual(mail.outbox[0].subject,
									 _(f"You are invited to register on %(site_name)s")%{'site_name':settings.SITE_NAME})
		for content, type in mail.outbox[0].alternatives:
			if type == 'text/html':
				break
		# print("content=", content)
		self.assertInHTML(_("Registration to the \"%(site_name)s\" site")%{'site_name':settings.SITE_NAME}, content)
		self.assertInHTML(f'''<h2 class="center">
			{_("Hello %(invited)s, this is %(admin)s!")%
				{'invited': test_invite['invited'], 'admin' : sender.get_full_name()}} <br/>
			{_("I invite you to register on the %(site_name)s website I created for managing our big family!")%
				{'site_name': settings.SITE_NAME}}
			</h2>''', content)
		mail.outbox = [] # reset test mailbox

	def test_invite_member_not_staff(self):
		# only superuser and staff cans send invites
		self.login()
		with self.assertRaises(PermissionError):
			self.do_test_invite(self.member)

	def test_invite_member_staff(self):
		self.account.is_staff = True # setUp
		self.account.save()
		self.do_test_invite(self.member)
		self.account.is_staff = False # tearDown
		self.account.save()

	def test_invite_member_superuser(self):
		self.superuser_login()
		self.do_test_invite(self.superuser.member)
		self.client.logout()
		self.login()

from captcha.conf import settings as captcha_settings
from django.test.utils import TestContextDecorator
class ignore_captcha_errors(TestContextDecorator):
	def __init__(self):
		super().__init__()
		self.captcha_test_mode = captcha_settings.CAPTCHA_TEST_MODE

	def enable(self):
		captcha_settings.CAPTCHA_TEST_MODE = True

	def disable(self):
		captcha_settings.CAPTCHA_TEST_MODE = self.captcha_test_mode

	def decorate_class(self, cls):
		from django.test import SimpleTestCase
		if not issubclass(cls, SimpleTestCase):
			raise ValueError(
				"Only subclasses of Django SimpleTestCase can be decorated "
				"with ignore_captcha_errors"
			)
		self.captcha_test_mode = captcha_settings.CAPTCHA_TEST_MODE
		return cls
	
class RequestRegistrationLinkTests(AccountTestCase):
	@ignore_captcha_errors()
	def test_request_registration(self):
		
		test_requester = { 'name': "Mr Freeze", 'email': 'test-cousinsmatter@maildrop.cc', 
										'message': "Hi, it's me!", 'captcha_0': 'whatever', 'captcha_1': 'passed' }
		response  = self.client.post(reverse("members:register_request"), test_requester, follow=True)
		self.assertContains(response, f'''<div class="message-body">{_("Registration request sent.")}</div>''', html=True)
		self.assertEqual(len(mail.outbox), 1)
		admin = User.objects.filter(is_superuser=True).first()
		self.assertIsNotNone(admin)
		self.assertSequenceEqual(mail.outbox[0].recipients(), [admin.email])
		self.assertEqual(mail.outbox[0].subject,_(f"Registration request for %(site_name)s")%{'site_name': settings.SITE_NAME})
		for content, type in mail.outbox[0].alternatives:
			if type == 'text/html':
				break
		# print(content)
		self.assertInHTML(_("Registration request for the \"%(site_name)s\" site")%{'site_name': settings.SITE_NAME}, content)
		self.assertInHTML(_("%(name)s (%(email)s) requested to register to your cousinades site")%
										{ 'name': test_requester['name'], 'email': test_requester['email']}, content)
		self.assertInHTML(f'''<div class="container">{test_requester['message']}</div>''', content) 
		request = RequestFactory().get('/dummy_path')
		absolute_link = request.build_absolute_uri(reverse("members:invite"))
		self.assertInHTML(f'''<a href="{absolute_link}?mail={test_requester['email']}" class="button green">{_("Open invitation page")}</a>''', content)
		mail.outbox = [] # reset test mailbox

	@ignore_captcha_errors()
	def test_request_registration_email_already_exists(self):
		test_requester = { 'name': "Mr Freeze", 'email': self.superuser_email, 
										'message': "Hi, it's me!", 'captcha_0': 'whatever', 'captcha_1': 'passed' }
		response  = self.client.post(reverse("members:register_request"), test_requester, follow=True)
		self.assertContains(response, f'''
<li class="message is-error">
  <div class="message-body">{_("User with this email already exists.")}</div>
</li>''', html=True)

	def test_request_registration_wrong_captcha(self):
		from ..forms import RegistrationRequestForm
		test_requester = { 'name': "Mr Freeze", 'email': 'test-cousinsmatter@maildrop.cc', 
										'message': "Hi, it's me!", 'captcha_0': 'whatever', 'captcha_1': 'whatever' }
		form = RegistrationRequestForm(test_requester)
		self.assertFormError(form, 'captcha', _("Invalid CAPTCHA"))

class MemberRegisterTests(AccountTestCase):

	def test_register_view_ok(self):
		factory = RequestFactory()
		request = factory.get('/dummy-path')
		email = 'test-cousinsmatter@maildrop.cc'
		invitation_url = RegistrationLinkManager().generate_link(request, email)
		response = self.client.get(invitation_url, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'members/member_upsert.html')
		self.assertContains(response, f'''<h1 class="title has-text-centered is-1">{_("Sign up")}</h1>''', html=True)

		user = { 'username': 'test_register_view', 'password1': self.password, 'password2': self.password,
					'first_name': self.first_name, 'last_name': self.last_name, 
					'email': 'test_register_view@test.com', 'phone': '01 23 45 67 78', "birthdate": date.today() }
		
		response = self.client.post(invitation_url, user, follow=True)
		self.assertContains(response, _('Hello %(username)s, your account has been created! You will now receive an email to verify your email address. Click in the link inside the mail to finish the registration.') % {"username": user['username']})
		
	def test_register_view_wrong_token(self):
		factory = RequestFactory()
		request = factory.get('/dummy-path')
		email = 'test-cousinsmatter@maildrop.cc'
		invitation_url = RegistrationLinkManager().generate_link(request, email) + 'wrong'
		response = self.client.get(invitation_url)
		self.assertContains(response, _("Invalid link. Please contact the administrator."), status_code=400)