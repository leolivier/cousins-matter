import re
import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.urls import reverse
from django.db.utils import IntegrityError
from django.utils.formats import localize
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core import mail
from verify_email.app_configurations import GetFieldFromSettings
from verify_email.views import verify_user_and_activate
from ..views.views_member import EditProfileView, MemberDetailView
from ..models import Member
from .tests_member_base import (
    TestLoginRequiredMixin,
    MemberTestCase,
    modify_member_data,
    get_new_member_data,
    today_minus,
)
from cm_main.utils import get_test_absolute_url


class UsersManagersTests(TestCase):
    def test_create_member(self):
        UserModel = get_user_model()
        self.assertEqual(UserModel, Member)
        member = UserModel.objects.create_member(
            username="foobar",
            email="normal@member.com",
            password="foo",
            first_name="foo",
            last_name="bar",
            privacy_consent=True,
        )
        self.assertEqual(member.email, "normal@member.com")
        self.assertFalse(member.is_active)
        self.assertFalse(member.is_staff)
        self.assertFalse(member.is_superuser)
        self.assertEqual(member.first_name, "foo")
        self.assertEqual(member.last_name, "bar")
        with self.assertRaises(TypeError):
            UserModel.objects.create_member()
        with self.assertRaises(TypeError):
            UserModel.objects.create_member(username="")
        with self.assertRaises(ValueError):
            UserModel.objects.create_member(
                username="",
                email="normal@member.com",
                password="foo",
                first_name="foo",
                last_name="bar",
            )
        # with self.assertRaises(ValueError):
        #     UserModel.objects.create_member(username="**+//", email="normal@member.com", password="foo",
        #                                     first_name='foo', last_name='bar')

    def test_create_superuser(self):
        UserModel = get_user_model()
        admin_user = UserModel.objects.create_superuser(
            username="superuser",
            email="super@member.com",
            password="foo",
            first_name="foo",
            last_name="bar",
            privacy_consent=True,
        )
        self.assertEqual(admin_user.email, "super@member.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        with self.assertRaises(ValueError):
            UserModel.objects.create_superuser(
                username="superuser",
                email="super@member.com",
                password="foo",
                is_superuser=False,
                first_name="foo",
                last_name="bar",
            )


class MemberViewTestMixin:
    def create_member_by_view(self, member_data=None):
        """creates and returns a new member through the UI using provided member data.
        Compared to create_member directly to DB, created users are supposed to be managed
        """
        member_data = member_data or get_new_member_data()
        response = self.client.post(reverse("members:create"), member_data, follow=True)
        self.assertEqual(response.status_code, 200)
        new_member = Member.objects.filter(username=member_data["username"]).first()
        self.assertIsNotNone(new_member)
        self.assertFalse(new_member.is_active)
        self.assertEqual(new_member.member_manager, self.member)
        self.created_members.append(new_member)
        return new_member


class MemberCreateTest(MemberViewTestMixin, MemberTestCase):
    def test_create_member_with_same_username(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Member.objects.create(username=self.member.username)

    def test_create_managed_member_in_view(self):
        prev_number = Member.objects.count()
        managed = self.create_member_by_view()
        new_number = Member.objects.count()
        # a new member has been created
        self.assertEqual(new_number, prev_number + 1)
        # managed is managed by the creating member
        self.assertEqual(managed.member_manager, self.member)


class MemberDeleteTest(MemberViewTestMixin, MemberTestCase):
    def test_delete_member(self):
        member = self.create_member()
        member.delete()
        self.assertEqual(Member.objects.filter(id=member.id).count(), 0)
        self.assertEqual(Member.objects.filter(username=member.username).count(), 0)

    def test_delete_member_by_view(self):
        member = self.create_member_by_view()
        response = self.client.post(
            reverse("members:delete", args=[member.id]), follow=True
        )
        self.assertContainsMessage(response, "info", _("Member deleted"))
        self.assertEqual(Member.objects.filter(id=member.id).count(), 0)
        self.assertEqual(Member.objects.filter(username=member.username).count(), 0)


class LoginRequiredTests(TestLoginRequiredMixin, TestCase):
    def test_login_required(self):
        for url in [
            "members:logout",
            "change_password",
            "members:members",
            "members:profile",
            "members:create",
            "members:birthdays",
        ]:
            self.assertRedirectsToLogin(url)
        for url in ["members:member_edit", "members:detail"]:
            self.assertRedirectsToLogin(url, args=(1,))


class MemberProfileViewTest(MemberTestCase):
    def test_member_profile_view(self):
        profile_url = reverse("members:profile")
        response = self.client.get(profile_url)
        # self.print_response(response)
        self.assertTemplateUsed(response, "members/members/member_upsert.html")
        self.assertIs(response.resolver_match.func.view_class, EditProfileView)

        self.assertContains(
            response,
            f"""<input type="text" name="username" value="{self.member.username}"
                      maxlength="150" class="input" required aria-describedby="id_username_helptext"
                      id="id_username">""",
            html=True,
        )
        self.assertContains(
            response,
            f"""<input type="text" name="first_name" value="{self.member.first_name}"
                      maxlength="150" class="input" id="id_first_name" required>""",
            html=True,
        )
        self.assertContains(
            response,
            f"""<input type="text" name="last_name" value="{self.member.last_name}"
                      maxlength="150" class="input" id="id_last_name" required>""",
            html=True,
        )

        self.assertTrue(self.member.is_active)
        self.assertIsNone(self.member.member_manager)
        new_data = modify_member_data(self.member)
        response = self.client.post(profile_url, new_data, follow=True)
        # print(vars(response))

        self.assertEqual(response.status_code, 200)
        self.member.refresh_from_db()
        # self.is_active becomes false because of the sending of the verification email (which changed)
        # self.assertTrue(self.member.is_active)
        # self.assertIsNone(self.member.member_manager)

        self.assertEqual(self.member.first_name, new_data["first_name"])
        self.assertEqual(self.member.phone, new_data["phone"])
        self.assertEqual(self.member.birthdate, new_data["birthdate"])
        self.assertEqual(self.member.email, new_data["email"])

    def test_avatar(self):
        from django.core.files.uploadedfile import InMemoryUploadedFile
        from io import BytesIO
        from PIL import Image
        import sys

        avatar_file = os.path.join(
            os.path.dirname(__file__), "resources", self.base_avatar
        )
        membuf = BytesIO()
        with Image.open(avatar_file) as img:
            img.save(membuf, format="JPEG", quality=90)
            size = sys.getsizeof(membuf)
            self.member.avatar = InMemoryUploadedFile(
                membuf, "ImageField", self.base_avatar, "image/jpeg", size, None
            )
        self.member.save()
        self.assertTrue(default_storage.exists(self.member.avatar.name))
        # reusing several times the same image which is renamed each time with a suffix
        testbn_prefix, test_ext = os.path.splitext(self.test_avatar_jpg)
        avatar_prefix, av_ext = os.path.splitext(self.member.avatar.name)
        avatar_prefix = os.path.relpath(avatar_prefix, settings.BASE_DIR)
        self.assertEqual(test_ext, test_ext)
        # print(avatar_prefix, testbn_prefix)
        self.assertTrue(avatar_prefix.startswith(testbn_prefix))
        # same for mini avatar
        mini_name = self.member.avatar_mini_name
        self.assertTrue(default_storage.exists(mini_name))
        testbn_prefix, test_ext = os.path.splitext(self.test_mini_avatar_jpg)
        avatar_prefix, av_ext = os.path.splitext(mini_name)
        avatar_prefix = os.path.relpath(avatar_prefix, settings.BASE_DIR)
        self.assertEqual(test_ext, test_ext)
        self.assertTrue(avatar_prefix.startswith(testbn_prefix))


class ManagedMemberChangeTests(MemberViewTestMixin, MemberTestCase):
    def setUp(self):
        super().setUp()
        # first create a new managed member
        self.managed = self.create_member_by_view()
        self.active = self.create_member(None, is_active=True)
        self.assertTrue(self.active.is_active)

    def tearDown(self):
        self.managed.delete()
        self.active.delete()
        super().tearDown()

    def test_managed_change_view(self):
        # change the managed member data
        edit_url = reverse("members:member_edit", kwargs={"pk": self.managed.id})
        new_data = modify_member_data(self.managed)
        response = self.client.post(edit_url, new_data, follow=True)
        # print(response.content.decode())
        self.assertEqual(response.status_code, 200)
        self.managed.refresh_from_db()
        self.assertEqual(self.managed.first_name, new_data["first_name"])
        self.assertEqual(self.managed.phone, new_data["phone"])
        self.assertEqual(self.managed.birthdate, new_data["birthdate"])
        self.assertEqual(self.managed.email, new_data["email"])

        # chack that active members can't be changed
        edit_url = reverse("members:member_edit", kwargs={"pk": self.active.id})
        new_data = modify_member_data(self.active)
        # for get
        response = self.client.get(edit_url, new_data, follow=True)
        self.assertEqual(response.status_code, 200)
        # self.print_response(response)
        self.assertContainsMessage(
            response, "error", _("You do not have permission to edit this member.")
        )
        self.assertRedirects(
            response, reverse("members:detail", kwargs={"pk": self.active.id})
        )
        # and post
        response = self.client.post(edit_url, new_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContainsMessage(
            response, "error", _("You do not have permission to edit this member.")
        )
        self.assertRedirects(
            response, reverse("members:detail", kwargs={"pk": self.active.id})
        )


class TestDisplayMembers(MemberTestCase):
    def setUp(self):
        super().setUp()
        # create several managed members
        self.members = [self.member]
        for __ in range(3):
            self.members.append(self.create_member())

    def test_view_one_member(self):
        member = self.members[3]
        detail_url = reverse("members:detail", kwargs={"pk": member.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        # pprint(vars(response))
        self.assertTemplateUsed(response, "members/members/member_detail.html")
        self.assertIs(response.resolver_match.func.view_class, MemberDetailView)
        active = (
            _("Active member")
            if member.is_active
            else _("Member managed by") + " " + member.member_manager.full_name
        )
        self.assertContains(
            response,
            f"""<p class="content small">{member.username}<br>( {active} )</p>""",
            html=True,
        )
        bdate = localize(member.birthdate, use_l10n=True)
        self.assertContains(
            response,
            f"""<tr>
          <td class="content has-text-right">{_("Birthdate")}</td>
          <td class="content">{bdate}</td>
        </tr>""",
            html=True,
        )

    def test_display_members(self):
        response = self.client.get(reverse("members:members"))
        html = (
            response.content.decode("utf-8")
            .replace("is-link", "")
            .replace("is-primary", "")
            .replace("is-dark", "")
        )
        # print(str(response.content))
        for i in range(len(self.members)):
            avatar = (
                ""
                if not self.members[i].avatar
                else f"""<figure class="image mini-avatar mr-2">
                      <img class="is-rounded" src="{self.members[i].avatar_mini_url}">
                     </figure>"""
            )
            self.assertInHTML(
                f"""
  <div class="cell has-text-centered my-auto">
    <a class="button button-wrap" href="/members/{self.members[i].id}/">
      {avatar}
      <strong>{self.members[i].full_name}</strong>
    </a>
  </div>
""",
                html,
            )

    def test_filter_members_display(self):
        def check_is_in(content, member):
            self.assertInHTML(
                f"""<div class="cell has-text-centered my-auto">
        <a class="button button-wrap" href="{reverse("members:detail", kwargs={"pk": member.id})}">
          <strong>{member.full_name}</strong></a></div>""",
                content,
            )

        def check_is_not_in(content, member):
            # no assertNotContains or assertNotInHTML in django yet
            self.assertNotIn(content, f"""<strong>{member.full_name}</strong>""")
            self.assertNotIn(
                content,
                f"""href={reverse("members:detail", kwargs={"pk": member.id})}>""",
            )

        def filter_member(member, first_name=False, last_name=False):
            filter = {}
            if first_name:  # remove first 4 chars
                if type(first_name) is bool:
                    first_name = member.first_name
                filter["first_name_filter"] = first_name[4:]
            if last_name:
                if type(last_name) is bool:
                    last_name = member.last_name
                filter["last_name_filter"] = last_name[4:]
            response = self.client.get(reverse("members:members"), filter)
            # print(response.content)
            self.assertEqual(response.status_code, 200)
            return (
                response.content.decode("utf-8")
                .replace("is-link", "")
                .replace("is-primary", "")
                .replace("is-dark", "")
            )

        member1 = self.create_member()
        member2 = self.create_member()
        member3 = self.create_member()
        accented_member = get_new_member_data()
        accented_filter = accented_member["first_name"] + "exxx "
        accented_member["first_name"] += "éxxx"
        member4 = self.create_member(accented_member)
        # can see all members when not filtered
        content = filter_member(None)
        # print(content)
        for member in [member1, member2, member3]:
            check_is_in(content, member)

        # filter on member1 first name part
        content = filter_member(member1, first_name=True)
        check_is_in(content, member1)
        check_is_not_in(content, member2)
        check_is_not_in(content, member3)
        check_is_not_in(content, member4)

        # filter on member2 last name part
        content = filter_member(member2, last_name=True)
        check_is_not_in(content, member1)
        check_is_in(content, member2)
        check_is_not_in(content, member3)
        check_is_not_in(content, member4)

        # filter on member3 first and last name part
        content = filter_member(member3, first_name=True, last_name=True)
        check_is_not_in(content, member1)
        check_is_not_in(content, member2)
        check_is_in(content, member3)
        check_is_not_in(content, member4)

        # check filters and striped spaces are ok
        content = filter_member(member4, first_name=accented_filter)
        check_is_not_in(content, member1)
        check_is_not_in(content, member2)
        check_is_not_in(content, member3)
        check_is_in(content, member4)

    def _check_member_order(self, response, members):
        html = (
            response.content.decode("utf-8")
            .replace("is-link", "")
            .replace("is-primary", "")
            .replace("is-dark", "")
        )
        content = ""
        for m in members:
            url = reverse("members:detail", kwargs={"pk": m.id})
            name = m.full_name
            content += f"""<div class="cell has-text-centered my-auto">
        <a class="button button-wrap" href="{url}">
          <strong>{name}</strong>
        </a>
      </div>"""
        self.assertInHTML(content, html)

    def test_sort_members(self):
        """
        Test that the members list page is sorted by last name, then first name by default
        or by the given sort criteria and order
        """
        self.create_member()
        self.create_member()
        self.create_member()
        # check default sort
        response = self.client.get(reverse("members:members"))
        self.assertEqual(response.status_code, 200)
        ms = Member.objects.all().order_by("last_name", "first_name")
        self._check_member_order(response, ms)
        # check sort by birthdate
        response = self.client.get(
            reverse("members:members"), {"member_sort": "birthdate"}
        )
        self.assertEqual(response.status_code, 200)
        ms = Member.objects.all().order_by("birthdate")
        self._check_member_order(response, ms)
        # check reverse order
        response = self.client.get(
            reverse("members:members"),
            {"member_sort": "birthdate", "member_order": "option2"},
        )
        self.assertEqual(response.status_code, 200)
        ms = Member.objects.all().order_by("-birthdate")
        self._check_member_order(response, ms)


class TestActivateManagedMember(MemberTestCase):
    def test_activate(self):
        managed = self.create_member()
        self.assertIsNotNone(managed)
        self.assertFalse(managed.is_active)
        self.assertEqual(managed.member_manager, self.member)
        mail.outbox = []
        response = self.client.post(
            reverse("members:activate", args=[managed.id]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        managed.refresh_from_db()
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertSequenceEqual(email.to, [managed.email])
        self.assertEqual(email.subject, GetFieldFromSettings().get("subject"))
        for content, type in email.alternatives:
            if type == "text/html":
                break
        s1 = _(
            "You received this mail because you attempted to create an account on our website or "
            "because a member created and activated your account"
        )
        s2 = _(
            "Please click on the link below to confirm the email and activate your account."
        )
        self.assertInHTML(f"""<p class="mt-2">{s1}<br>{s2}</p>""", content)
        url = reverse(
            verify_user_and_activate, args=["XXX_encoded_email__XXX", "XXX_token_XXX"]
        )
        url = (
            get_test_absolute_url(
                url.replace("/XXX_encoded_email__XXX/XXX_token_XXX", "")
            )
            + r'[^"]+'
        )
        # print('url:', url, 'content', content)
        match = re.search(url, content)
        self.assertIsNotNone(match)
        url = match.group(0)
        # print('url:', url)
        response = self.client.get(url, follow=True)
        tr1 = f"{_('Your Email is verified successfully and your account has been activated.')}"
        tr2 = f"{_('You can sign in with your credentials now...')}"
        self.assertContains(
            response,
            f'<p class="content">{tr1}</p><p class="content">{tr2}</p>',
            html=True,
        )
        managed.refresh_from_db()
        self.assertTrue(managed.is_active)


class TestDeadMembers(MemberViewTestMixin, MemberTestCase):
    def get_dead_member_data(self):
        data = get_new_member_data()
        # set death date 5 days ago
        data["deathdate"] = today_minus("5d")
        return data

    def check_dead_member(self, member):
        self.assertFalse(member.is_active)
        self.assertTrue(member.is_dead)
        # member manager can be self.member (ie member creator) or superuser
        self.assertIn(member.member_manager.id, [self.member.id, self.superuser.id])
        self.assertIsNotNone(member.deathdate)
        self.assertGreater(member.deathdate, member.birthdate)

    def test_create_dead_member(self):
        data = self.get_dead_member_data()
        dead = self.create_member(data)
        self.check_dead_member(dead)

    def test_post_dead_member(self):
        data = self.get_dead_member_data()
        dead = self.create_member_by_view(data)
        self.check_dead_member(dead)

    def test_update_dead_member(self):
        user = self.create_member()
        # change the managed member data
        edit_url = reverse("members:member_edit", kwargs={"pk": user.id})
        new_data = modify_member_data(user)
        # set deathdate
        new_data["deathdate"] = today_minus("5d")
        response = self.client.post(edit_url, new_data, follow=True)
        # print(response.content.decode())
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.check_dead_member(user)

        # check that dead members can't be activated
        activate_url = reverse("members:activate", kwargs={"pk": user.id})
        response = self.client.get(activate_url, follow=True)
        self.assertEqual(response.status_code, 200)
        # self.print_response(response)
        self.assertContainsMessage(
            response, "error", _("Error: Cannot activate a dead member ")
        )
        self.assertRedirects(
            response, reverse("members:detail", kwargs={"pk": user.id})
        )

    def test_display_dead_members(self):
        data = self.get_dead_member_data()
        dead = self.create_member(data)
        self.check_dead_member(dead)
        dead_url = reverse("members:detail", kwargs={"pk": dead.id})
        response = self.client.get(dead_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            """<span class="icon is-large">
    <i class="mdi mdi-24px mdi-shield-cross-outline" aria-hidden="true"></i>
</span>""",
            html=True,
        )
        deathdate = localize(dead.deathdate, use_l10n=True)
        self.assertContains(
            response,
            f"""<tr>
    <td class="content has-text-right">{_("Deceased on")}</td>
    <td class="content">{deathdate}</td>
  </tr>""",
            html=True,
        )
