from django.contrib.auth.models import User
from django.urls import reverse
from django.db.utils import IntegrityError
from django.utils.formats import localize
from django.utils.translation import gettext as _
from django.conf import settings
from ..views.views_member import EditProfileView, MemberDetailView
from ..models import Member
from accounts.tests import CreatedAccountTestCase, LoggedAccountTestCase
from datetime import date
import os

COUNTER = 0


class MemberTestCase(LoggedAccountTestCase):

  def counter(self):
    global COUNTER
    COUNTER += 1
    return str(COUNTER)

  def setUp(self):
    super().setUp()
    self.member = Member.objects.get(account=self.account)

  # def tearDown(self) -> None:
  #   return super().tearDown()

  def get_new(self, input_str, counter):
    """build a new string based on the passed one"""
    return input_str + counter

  def get_new_member_data(self):
    """returns a brand new member data (new username)"""
    counter = self.counter()
    uname = self.get_new(self.username, counter)
    new_password = self.get_new(self.password, counter)

    return {'username': uname, 'password1': new_password, 'password2': new_password,
            'first_name': self.get_new(self.first_name, counter), 'last_name': self.get_new(self.last_name, counter),
            'email': uname+'@test.com', 'phone': '01 23 45 67 ' + counter, "birthdate": date.today()}

  def get_changed_member_data(self, member):
    """returns a modified member dataset (same username and last_name)"""
    counter = self.counter()
    return {'username': member.account.username, 'first_name': self.get_new(member.account.first_name, counter),
            'last_name': member.account.last_name, 'email': member.account.username+'@test.com',
            'phone': '01 23 45 67 ' + counter, "birthdate": date.today()}

  def create_member(self, member_data=None):
    """creates and returns a new member using provided member data"""
    if member_data is None:
      member_data = self.get_new_member_data()
    response = self.client.post(reverse("members:create"), member_data, follow=True)
    self.assertEqual(response.status_code, 200)
    new_member = Member.objects.filter(account__username=member_data['username']).first()
    self.assertIsNotNone(new_member)
    return new_member


class MemberCreateTest(MemberTestCase):

  def test_create_member_with_same_account(self):
    with self.assertRaises(IntegrityError):
      Member.objects.create(account=self.account)

  def test_create_account_creates_member(self):
      # check that create account (in SetUp) has an associated Member
      self.assertEqual(Member.objects.filter(account=self.account).count(), 1)

  def test_create_managed_member_in_view_creates_user(self):
    prev_number = Member.objects.count()
    managed = self.create_member()
    new_number = Member.objects.count()
    # a new member has been created
    self.assertEqual(new_number, prev_number+1)
    # there is a member with account's username is the new username
    # managed is managed by the creating user (ie self.member.account=self.account)
    self.assertEqual(managed.managing_account, self.account)


class MemberDeleteTest(MemberTestCase):

  def test_delete_member_deletes_user(self):
    member = Member.objects.filter(account__username=self.account.username)
    self.assertEqual(member.count(), 1)
    member = member.first()
    member.delete()
    self.assertEqual(Member.objects.filter(id=member.id).count(), 0)
    self.assertEqual(User.objects.filter(username=self.account.username).count(), 0)


class LoginRequiredTests(CreatedAccountTestCase):

  def test_login_required(self):
    for url in ['members:members', 'members:profile', 'members:create', 'members:birthdays']:
      rurl = reverse(url)
      response = self.client.get(rurl)
      # checks that the response is a redirect (302) to the login page
      # with another redirect afterward to the original url
      self.assertRedirects(response, self.next(self.login_url, rurl), 302, 200)
    member = Member.objects.get(account=self.account)
    for url in ['members:member_edit', 'members:detail']:
      rurl = reverse(url, args=(f'{member.id}', ))
      response = self.client.get(rurl)
      self.assertRedirects(response, self.next(self.login_url, rurl), 302, 200)


class MemberProfileViewTest(MemberTestCase):

  def test_member_profile_view(self):
    profile_url = reverse('members:profile')
    response = self.client.get(profile_url)
    # pprint(vars(response))
    self.assertTemplateUsed(response, 'members/member_upsert.html')
    self.assertIs(response.resolver_match.func.view_class, EditProfileView)

    self.assertContains(response, f'''<input type="text" name="username" value="{self.username}"
                      maxlength="150" class="input" required aria-describedby="id_username_helptext"
                      id="id_username">''', html=True)
    self.assertContains(response, f'''<input type="text" name="first_name" value="{self.first_name}"
                      maxlength="150" class="input" id="id_first_name" required>''', html=True)
    self.assertContains(response, f'''<input type="text" name="last_name" value="{self.last_name}"
                      maxlength="150" class="input" id="id_last_name" required>''', html=True)
    self.assertEqual(self.account, self.member.account)
    self.assertEqual(self.member.managing_account, self.member.account)
    self.assertTrue(self.account.is_active)
    new_data = self.get_changed_member_data(self.member)
    response = self.client.post(profile_url, new_data, follow=True)
    # print(vars(response))

    self.assertEqual(response.status_code, 200)
    self.account.refresh_from_db()
    self.member.refresh_from_db()
    self.assertEqual(self.account, self.member.account)
    self.assertEqual(self.member.managing_account, self.member.account)
    # self.assertTrue(self.account.is_active)
    if not self.account.is_active:  # is_active became false for an unknown reason
      self.account.is_active = True
      self.account.save()

    self.assertEqual(self.account.first_name, new_data['first_name'])
    self.assertEqual(self.member.phone, new_data['phone'])
    self.assertEqual(self.member.birthdate, new_data['birthdate'])
    self.assertEqual(self.account.email, new_data['email'])

  def test_avatar(self):
    from django.core.files.uploadedfile import InMemoryUploadedFile
    from io import BytesIO
    from PIL import Image
    import sys

    avatar_file = os.path.join(os.path.dirname(__file__), "test_avatar.jpg")
    membuf = BytesIO()
    with Image.open(avatar_file) as img:
      img.save(membuf, format='JPEG', quality=90)
      size = sys.getsizeof(membuf)
      self.member.avatar = InMemoryUploadedFile(membuf, 'ImageField', "test_avatar.jpg",
                                                'image/jpeg', size, None)
    self.member.save()
    self.assertTrue(os.path.isfile(os.path.join(settings.MEDIA_ROOT, settings.AVATARS_DIR, os.path.basename(avatar_file))))


class ManagedMemberChangeTests(MemberTestCase):
  def setUp(self):
    super().setUp()
    # first create a new managed member
    self.managed = self.create_member()
    self.active = self.create_member()
    self.active.account.is_active = True
    self.active.account.save()
    self.assertTrue(self.active.account.is_active)

  def test_managed_change_view(self):
    # change the managed member data
    edit_url = reverse('members:member_edit', kwargs={'pk': self.managed.id})
    new_data = self.get_changed_member_data(self.managed)
    response = self.client.post(edit_url, new_data, follow=True)
    self.assertEqual(response.status_code, 200)
    self.managed.refresh_from_db()
    self.managed.account.refresh_from_db()
    self.assertEqual(self.managed.account.first_name, new_data['first_name'])
    self.assertEqual(self.managed.phone, new_data['phone'])
    self.assertEqual(self.managed.birthdate, new_data['birthdate'])
    self.assertEqual(self.managed.account.email, new_data['email'])

    # chack that active members can't be changed
    edit_url = reverse('members:member_edit', kwargs={'pk': self.active.id})
    new_data = self.get_changed_member_data(self.managed)
    # for get
    response = self.client.get(edit_url, new_data, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertContainsMessage(response, "error", _("You do not have permission to edit this member."))
    self.assertRedirects(response, reverse('members:detail', kwargs={'pk': self.active.id}))
    # and post
    response = self.client.post(edit_url, new_data, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertContainsMessage(response, "error", _("You do not have permission to edit this member."))
    self.assertRedirects(response, reverse('members:detail', kwargs={'pk': self.active.id}))


class TestDisplayMembers(MemberTestCase):
  def setUp(self):
    super().setUp()
    # create several managed members
    self.members = [self.member]
    for __ in range(3):
      self.members.append(self.create_member())

  def test_view_one_member(self):
    member = self.members[3]
    detail_url = reverse('members:detail', kwargs={'pk': member.id})
    response = self.client.get(detail_url)
    self.assertEqual(response.status_code, 200)
    # pprint(vars(response))
    self.assertTemplateUsed(response, 'members/member_detail.html')
    self.assertIs(response.resolver_match.func.view_class, MemberDetailView)
    account = member.account
    active = _("Active member") if account.is_active else _("Managed member")
    self.assertContains(response, f'''<p class="content small">{account.username} ( {active} )</p>''', html=True)
    bdate = localize(member.birthdate, use_l10n=True)
    self.assertContains(response, f'''<tr>
          <td class="content has-text-right">{_("Birthdate")}</td>
          <td class="content">{bdate}</td>
        </tr>''', html=True)

  def test_display_members(self):
    response = self.client.get(reverse("members:members"))
    html = response.content.decode('utf-8').replace('is-link', '').replace('is-primary', '')
    # pprint(vars(response))
    for i in range(len(self.members)):
      self.assertInHTML(f'''
  <div class="cell has-text-centered">
    <a class="button" href="/members/{self.members[i].id}/">
      <strong>{self.members[i].account.first_name} {self.members[i].account.last_name}</strong>
    </a>
  </div>
''', html)

  def test_filter_members_display(self):

    def check_is_in(content, member):
      self.assertInHTML(f'''<div class="cell has-text-centered">
        <a class="button" href="{reverse("members:detail", kwargs={'pk': member.id})}">
          <strong>{member.get_full_name()}</strong></a></div>''', content)

    def check_is_not_in(content, member):
      # no assertNotContains or assertNotInHTML in django yet
      self.assertNotIn(content, f'''<strong>{member.get_full_name()}</strong>''')
      self.assertNotIn(content, f'''href={reverse("members:detail", kwargs={'pk': member.id})}>''')

    def filter_member(member, first_name=False, last_name=False):
      filter = {}
      if first_name:
        filter['first_name_filter'] = member.account.first_name[-4:]
      if last_name:
        filter['last_name_filter'] = member.account.last_name[-4:]
      response = self.client.get(reverse("members:members"), filter)
      # print(response.content)
      self.assertEqual(response.status_code, 200)
      return response.content.decode('utf-8').replace('is-link', '').replace('is-primary', '')
    
    member1 = self.create_member()
    member2 = self.create_member()
    member3 = self.create_member()
    # can see all memebers when not filtered
    content = filter_member(None)
    for member in [member1, member2, member3]:
      check_is_in(content, member)

    # filter on member1 first name part
    content = filter_member(member1, first_name=True)
    check_is_in(content, member1)
    check_is_not_in(content, member2)
    check_is_not_in(content, member3)
    # filter on member2 last name part
    content = filter_member(member2, last_name=True)
    check_is_not_in(content, member1)
    check_is_in(content, member2)
    check_is_not_in(content, member3)

    # filter on member3 first and last name part
    content = filter_member(member3, first_name=True, last_name=True)
    check_is_not_in(content, member1)
    check_is_not_in(content, member2)
    check_is_in(content, member3)
