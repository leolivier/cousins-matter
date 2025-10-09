from datetime import datetime, timedelta
import os
from urllib.parse import urlencode
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user
from django.test import RequestFactory, TestCase

from ..models import Member

COUNTER: int = -1  # -1 for superuser and 0 for member


def get_counter():
  global COUNTER
  res = COUNTER
  COUNTER += 1
  return res


def get_fake_request():
    return RequestFactory().get('/dummy-path')


def today_minus(delta: str):
    unit = delta[-1]
    value = int(delta[:-1])
    units = {'d': 'days', 'w': 'weeks'}
    try:
      match unit:
        case 'y':
          unit = 'days'
          value *= 365
        case 'm':
          unit = 'days'
          value *= 30
        case _:
          unit = units[unit]
    except KeyError:
      raise ValueError("Invalid delta unit")
    dt = datetime.today() - timedelta(**{unit: value})
    return dt.date()


def get_new_member_data(**kwargs):
  """returns a brand new member data (new username)""" 
  counter = get_counter()
  prefix = kwargs.get('prefix', '')
  return {
    'username': kwargs.get('username', f'{prefix}foobar{counter}'),
    'password': kwargs.get('password', f'{prefix}vWx12/gtV"{counter}'),
    'email': kwargs.get('email', f'{prefix}foo{counter}@bar.com'),
    'first_name': kwargs.get('first_name', f'{prefix}foo{counter}'),
    'last_name': kwargs.get('last_name', f'{prefix}bar{counter}'),
    'phone': kwargs.get('phone', f'01 23 45 67 {counter}'),
    "birthdate": kwargs.get('birthdate', today_minus(f'{counter}y')),
    "privacy_consent": kwargs.get('privacy_consent', True)
  }


def modify_member_data(member):
  """returns a modified member dataset (same username and last_name, don't change deathdate)"""
  counter = get_counter()
  return {
    'username': member.username,
    'first_name': f'{member.first_name}{counter}',
    'last_name': member.last_name,
    'email': f'{member.username}{counter}@test.com',
    'phone': f'01 23 45 67 {counter}',
    "birthdate": today_minus(f'{counter}y'),  # counter has changed so birthdate changes
    "privacy_consent": member.privacy_consent,
    "deathdate": member.deathdate or ''
  }


class MemberTestCase(TestCase):
  member = None
  superuser = None

  login_url = reverse('members:login')
  logout_url = reverse('members:logout')
  change_password_url = reverse('change_password')

  base_avatar = "test_avatar.jpg"
  test_avatar_jpg = os.path.join(settings.MEDIA_ROOT, settings.AVATARS_DIR, "test_avatar.jpg")
  test_mini_avatar_jpg = os.path.join(settings.MEDIA_ROOT, settings.AVATARS_DIR, "mini_test_avatar.jpg")

  @classmethod
  def setUpTestData(cls):
    "called once by the test framework before running the tests"
    # create a superuser for testing
    superuser_data = get_new_member_data(prefix="superuser-")
    # force username
    superuser_data['username'] = 'superuser'
    pwd = superuser_data['password']
    cls.superuser = Member.objects.create_superuser(**superuser_data)
    cls.superuser.password = pwd  # keep unhashed password in memory for login

    # create a member for testing
    member_data = get_new_member_data()
    pwd = member_data['password']
    member_data['is_active'] = True
    cls.member = Member.objects.create_member(**member_data)
    cls.member.password = pwd  # keep unhashed password in memory for login

  def setUp(self):
    super().setUp()
    self.created_members = []
    self.client.login(username=self.member.username, password=self.member.password)

  def tearDown(self):
    for m in self.created_members:
      if m.id is not None:
        m.delete()
    self.created_members = []
    self.client.logout()
    return super().tearDown()

  @staticmethod
  def print_response(response):
    print('*'*80)
    print(response.content.decode().replace('\\t', '\t').replace('\\n', '\n'))
    print('*'*80)

  def current_user(self):
    return get_user(self.client)

  def assertMemberExists(self, member):
    self.assertTrue(Member.objects.filter(username=member.username).exists())

  def assertRequestUserIsLogged(self):
    self.assertTrue(self.current_user().is_authenticated)

  def assertRequestUserIsNotLogged(self):
    self.assertFalse(self.current_user().is_authenticated)

  def assertContainsMessage(self, response, type, message):
    self.assertContains(response, f'''<li class="message is-{type}">
      <div class="message-body">{message}
      </div>
    </li>''', html=True)

  def create_member(self, member_data=None, is_active=False):
    """creates and returns a new member using provided member data.
    If the member data is None, a new one is created.
    """
    member_data = member_data or get_new_member_data()
    pwd = member_data['password']
    new_member = Member.objects.create_member(**member_data, is_active=is_active,
                                              member_manager=None if is_active else self.member)
    new_member.password = pwd  # keep unhashed password in memory for login
    self.created_members.append(new_member)
    return new_member

  async def acreate_member(self, member_data=None, is_active=False):
    """asynchronously creates and returns a new member using provided member data.
    If the member data is None, a new one is created.
    """
    member_data = member_data or get_new_member_data()
    pwd = member_data.get('password')
    new_member = Member.objects.acreate_member(**member_data, is_active=is_active,
                                               member_manager=None if is_active else self.member)
    new_member.password = pwd  # keep unhashed password in memory for login
    self.created_members.append(new_member)
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
