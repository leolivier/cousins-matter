from datetime import datetime, timedelta
import os
from urllib.parse import urlencode
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user
from django.test import RequestFactory, TestCase

from ..models import Member

COUNTER = 0


def get_counter():
  global COUNTER
  COUNTER += 1
  # print('count=', COUNTER)
  return str(COUNTER)


def get_fake_request():
    return RequestFactory().get('/dummy-path')


def yesterday(ndays=1):
    today = datetime.today()
    yester_day = today - timedelta(days=ndays)
    return yester_day.date()


class MemberTestCase(TestCase):
  member = None
  username = 'foobar'
  password = 'vWx12/gtV"'
  email = "foo@bar.com"
  first_name = "foo"
  last_name = "bar"

  superuser = None
  superuser_name = "superuser"
  superuser_pwd = "SuPerUser1!"
  superuser_email = "superuser@test.com"

  login_url = reverse('members:login')
  logout_url = reverse('members:logout')
  change_password_url = reverse('change_password')

  base_avatar = "test_avatar.jpg"
  test_avatar_jpg = os.path.join(settings.MEDIA_ROOT, settings.AVATARS_DIR, "test_avatar.jpg")
  test_mini_avatar_jpg = os.path.join(settings.MEDIA_ROOT, settings.AVATARS_DIR, "mini_test_avatar.jpg")

  @classmethod
  def setUpTestData(cls):
    cls.superuser = Member.objects.create_superuser(cls.superuser_name, cls.superuser_email, cls.superuser_pwd,
                                                    "Super", "Member", privacy_consent=True)
    cls.member = Member.objects.create_member(cls.username, cls.email, cls.password,
                                              cls.first_name, cls.last_name, is_active=True, privacy_consent=True)

  def setUp(self):
    super().setUp()
    self.created_members = []
    self.login()  # login as self.member

  def tearDown(self):
    for m in self.created_members:
      if m.id is not None:
        m.delete()
    self.created_members = []
    return super().tearDown()

  def print_response(self, response):
    print('*'*80)
    print(response.content.decode().replace('\\t', '\t').replace('\\n', '\n'))
    print('*'*80)

  def login(self):
    self.client.logout()
    self.assertMemberExists()
    member = get_user(self.client)
    logged = member.is_authenticated or self.client.login(username=self.username, password=self.password)
    self.assertTrue(logged)

  def login_as(self, member):
    # 1rst logout then login as member
    self.client.logout()
    logged = self.client.login(username=member.username, password=member.password)
    self.assertTrue(logged)
    current_member = get_user(self.client)
    self.assertEqual(current_member.username, member.username)
    self.assertTrue(current_member.is_authenticated)

  def current_member(self):
    return get_user(self.client)

  def assertMemberExists(self):
    self.assertTrue(Member.objects.filter(username=self.username).exists())

  def assertMemberIsLogged(self):
    member = get_user(self.client)
    self.assertTrue(member.is_authenticated)

  def assertMemberIsNotLogged(self):
    member = get_user(self.client)
    self.assertFalse(member.is_authenticated)

  def superuser_login(self):
    self.assertIsNotNone(self.superuser)
    member = get_user(self.client)
    if member.is_authenticated and not member.is_superuser:
      self.client.logout()
      member = get_user(self.client)  # is refresh needed?
    logged = member.is_authenticated or self.client.login(username=self.superuser_name, password=self.superuser_pwd)
    self.assertTrue(logged)

  def assertContainsMessage(self, response, type, message):
    self.assertContains(response, f'''<li class="message is-{type}">
      <div class="message-body">{message}
      </div>
    </li>''', html=True)

  def _get_new(self, input_str, counter):
    """build a new string based on the passed one"""
    return input_str + counter

  def get_new_member_data(self):
    """returns a brand new member data (new username)"""
    counter = get_counter()
    uname = self._get_new(self.username, counter)
    new_password = self._get_new(self.password, counter)

    return {'username': uname, 'password': new_password, 'email': uname+'@test.com',
            'first_name': self._get_new(self.first_name, counter), 'last_name': self._get_new(self.last_name, counter),
            'phone': '01 23 45 67 ' + counter, "birthdate": yesterday(3000), "privacy_consent": True}

  def get_changed_member_data(self, member):
    """returns a modified member dataset (same username and last_name, don't change deathdate)"""
    counter = get_counter()
    return {'username': member.username, 'first_name': self._get_new(member.first_name, counter),
            'last_name': member.last_name, 'email': member.username+'@test.com',
            'phone': '01 23 45 67 ' + counter, "birthdate": yesterday(2000), "privacy_consent": True, 
            "deathdate": member.deathdate or ''}

  def create_member(self, member_data=None, is_active=False):
    """creates and returns a new member using provided member data.
    If the member data is None, a new one is created.
    """
    if member_data is None:
      member_data = self.get_new_member_data()
      # save password before hashing
      passwd = member_data['password']
    else:
      passwd = member_data['password']
    new_member = Member.objects.create_member(**member_data, is_active=is_active,
                                              member_manager=None if is_active else self.member)
    # store real password instead of hashed one so that we can login with it afterward
    new_member.password = passwd
    self.created_members.append(new_member)
    return new_member

  def create_member_and_login(self, member_data=None):
    """creates and returns a new member using provided member data.
    If the member data is None, a new one is created.
    The user is set as active and logged in by the method"""
    new_member = self.create_member(member_data, is_active=True)
    self.login_as(new_member)
    return new_member


class TestLoginRequiredMixin():
  login_url = reverse('members:login')

  def next(self, from_url, to_url):
    return f"{from_url}?{urlencode({'next': to_url})}"

  def assertRedirectsToLogin(self, url, args=None):
    """checks that getting the provided url w/o being logged
       afterward to the original url"""
    rurl = reverse(url, args=args)
    response = self.client.get(rurl)
    self.assertRedirects(response, self.next(self.login_url, rurl), 302, 200)
