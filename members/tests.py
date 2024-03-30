from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from pprint import pprint

from .models import Member, Address, Family

TEST_ACCOUNT={'username': 'foobar', 'password': 'vWx12/gtV"',  "email": "foo@bar.com",
					 "first_name": "foo", "last_name": "bar" }

def sreverse(url):
	return reverse(url).rstrip('/')

class MemberCreateTest(TestCase):
	def setUp(self):
		global TEST_ACCOUNT
		self.account = User.objects.create_user(**TEST_ACCOUNT)

	# def test_create_member(self):
	# 	member = Member.objects.create(account=User.objects.create(username='test', password='<PASSWORD>'))
	# 	self.assertEqual(member.account.username, 'test')
	# 	self.assertEqual(member.account.password, '<PASSWORD>')

	def test_create_user_creates_member(self):
			# check taht create account (in SetUp) has an associated Member
			self.assertEqual(Member.objects.filter(account=self.account).count(), 1)

	def test_create_managed_member_creates_user(self):
		global TEST_ACCOUNT
		manager = TEST_ACCOUNT.copy()
		manager['username'] += '1'
		managed = TEST_ACCOUNT.copy()
		managed['username'] += '2'
		manager = User.objects.create_user(**manager)
		managed = Member.objects.create(managing_account=manager)
		# managed is managed by manager
		self.assertEqual(managed.managing_account, manager)
		# managed has an account associated with it
		self.assertTrue(hasattr(managed, 'account'))
		# exactly one account associated to new member
		self.assertEqual(User.objects.filter(username=managed.account.username).count(), 1)
		# exactly one member associated to manager (true only in testing mode)
		self.assertEqual(Member.objects.filter(managing_account=manager).count(), 1)

	def test_delete_member_deletes_user(self):
		member = Member.objects.filter(account__username=self.account.username)
		self.assertEqual(member.count(), 1)
		member = member.first()
		member.delete()
		self.assertEqual(Member.objects.filter(id=member.id).count(), 0)
		self.assertEqual(User.objects.filter(username=self.account.username).count(), 0)


class LoginRequiredTests(TestCase):
	def setUp(self):
		global TEST_ACCOUNT
		account = User.objects.create_user(**TEST_ACCOUNT)
		self.member = Member.objects.filter(account=account).first()
		
	def test_login_required(self):
		racc = sreverse('accounts:login')
		for url in ['members:members', 'members:profile', 'members:create', 'members:birthdays']:
			rurl = reverse(url)
			response = self.client.get(rurl)
			# checks that the response is a redirect (302) to the login page 
			# with another redirect afterwaud to the original url
			self.assertRedirects(response, f"{racc}?next={rurl}", 302, 301)
		for url in ['members:edit', 'members:detail']:
			rurl = reverse(url, args=(f'{self.member.id}',))
			response = self.client.get(rurl)
			self.assertRedirects(response, f"{racc}?next={rurl}", 302, 301)

class MemberProfileViewTest(TestCase):
	def setUp(self):
		global TEST_ACCOUNT
		account = User.objects.create_user(**TEST_ACCOUNT)
		self.member = Member.objects.filter(account=account).first()
		self.credentials = {'username': TEST_ACCOUNT['username'], 'password': TEST_ACCOUNT['password']}

	def test_member_profile_view(self):
		global TEST_ACCOUNT
		# first login
		response = self.client.post(reverse('accounts:login'), self.credentials, follow=True)

		response = self.client.get(reverse('members:profile'))
		# pprint(vars(response))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response,'members/member_detail.html')
		self.assertContains(response, self.member.account.username)
		self.assertContains(response, self.member.account.first_name)
		user = TEST_ACCOUNT.copy()
		user['first_name'] += '1'
		user['phone'] = '01 23 45 67 89'
		response = self.client.post(reverse('members:profile'), user, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(User.objects.get(username=user['username']).first_name, user['first_name'])
		self.assertEqual(Member.objects.get(account__username=user['username']).phone, user['phone'])