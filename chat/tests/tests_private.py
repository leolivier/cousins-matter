import random
from urllib.parse import urlencode
import re

from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import gettext as _, ngettext

from members.tests.tests_member_base import MemberTestCase
from ..models import ChatMessage, ChatRoom, PrivateChatRoom
from cm_main.templatetags.cm_tags import icon


class PrivateChatRoomTestsMixin:
    def get_lists_buttons(self, slug):
        members_icon = icon("members")
        return f"""
  <a class="button" href="{reverse('chat:private_room_members', args=[slug])}">
    {members_icon} <span>{_('Room Members')}</span>
  </a>
  <a class="button" href="{reverse('chat:private_room_admins', args=[slug])}">
    {members_icon} <span>{_('Room Admins')}</span>
  </a>"""

    def do_check_private_chat_room(self, room_name):
        slug = slugify(room_name)
        url = reverse("chat:new_private_room") + "?" + urlencode({"name": room_name})
        response = self.client.get(url, follow=True)
        # self.print_response(response)
        # should be redirected to room detail. if not, it means there was an error
        self.assertTemplateUsed(response, "chat/room_detail.html")
        self.assertContains(
            response, f'<span id="show-room-name">{room_name}</span>', html=True
        )

        self.assertContains(response, self.get_lists_buttons(slug), html=True)
        rooms = ChatRoom.objects.filter(slug=slug)
        self.assertEqual(rooms.count(), 1)
        room = PrivateChatRoom.objects.get(name=room_name)
        self.assertEqual(room.slug, slug)
        return room

    def check_private_chat_room_list(self, response, room, nmsgs, nmembers):
        profile = _("profile")
        admin = room.admins.first()
        self.assertIsNotNone(admin)
        tr_nmsgs = ngettext("%(nmsgs)s message", "%(nmsgs)s messages", nmsgs) % {
            "nmsgs": nmsgs
        }
        tr_nmembers = ngettext(
            "%(nfollowers)s member", "%(nfollowers)s members", nmembers
        ) % {"nfollowers": nmembers}
        self.assertContains(
            response,
            f"""
<div class="panel-block is-flex is-flex-wrap-wrap is-align-items-flex-start">
  <div class="panel-icon mini-avatar is-flex is-align-items-center is-justify-content-center is-flex-shrink-5 image">
    <img class="is-rounded" src="{self.member.avatar_mini_url}" alt="{self.member.username}">
  </div>
  <div class="is-flex-shrink-1 has-text-primary has-text-weight-bold mr-5">
    {admin.full_name}
    <a href="{reverse('members:detail', args=[admin.id])}" aria-label="{profile}">
      {icon("member-link")}
    </a>
    <br>
    <span class="tag mr-3">{tr_nmsgs}</span>
    <span class="tag ">{tr_nmembers}</span>
  </div>
  <div class="is-flex-grow-1">
    <a class="title is-size-6" href="{reverse('chat:private_room', args=[room.slug])}">{room.name}</a>
  </div>
  <div class="mr-1 buttons has-addons is-rounded">
  {self.get_lists_buttons(room.slug)}
  </div>
</div>
""",
            html=True,
        )

    def get_leave_text(self, room):
        leave_room = _("Leave this room")
        areyousure = _("Are you sure you want to leave this room?")

        return f"""
    <button class="button"
    onclick="confirm_and_redirect('{areyousure}', '{reverse('chat:leave_private_room', args=[room.slug])}')"
    title="{leave_room}">
    {icon('leave-group')}
    <span class="is-hidden-mobile">{leave_room}</span>
  </button>"""

    def get_remove_text(self, room, member, is_admin=False):
        if is_admin:
            remove_member = _("Remove Admin from Room")
            areyousure = _("Are you sure you want to remove this admin from the room?")
            remove_url = reverse(
                "chat:remove_admin_from_private_room", args=[room.slug, member.id]
            )
        else:
            remove_member = _("Remove Member from Room")
            areyousure = _("Are you sure you want to remove this member from the room?")
            remove_url = reverse(
                "chat:remove_member_from_private_room", args=[room.slug, member.id]
            )

        return f"""
<button class="button"
    onclick="confirm_and_redirect('{areyousure}', '{remove_url}')"
    title="{remove_member}">
  {icon('leave-group')}
  <span>{remove_member}</span>
</button>"""

    def check_private_members_list(self, response, room, member):
        self.assertContains(
            response,
            f"""
<div class="panel-block is-flex is-flex-wrap-wrap is-align-items-flex-start">
  <div class="panel-icon mini-avatar is-flex is-align-items-center is-justify-content-center is-flex-shrink-5 image">
    <img class="is-rounded" src="{member.avatar_mini_url}"	alt="{member.username}">
  </div>
  <div class="has-text-primary has-text-weight-bold has-text-left is-flex-grow-1 mr-5">
    {member.full_name}
    <a href="{reverse('members:detail', args=[member.id])}" aria-label="{_('profile')}">
      {icon("member-link")}
    </a>
  </div>
  {self.get_remove_text(room, member)}
</div>""",
            html=True,
        )

    def check_private_admins_list(self, response, room, admin):
        self.assertContains(
            response,
            f"""
<div class="panel-block is-flex is-flex-wrap-wrap is-align-items-flex-start">
  <div class="panel-icon mini-avatar is-flex is-align-items-center is-justify-content-center is-flex-shrink-5 image">
    <img class="is-rounded" src="{admin.avatar_mini_url}"	alt="{admin.username}">
  </div>
  <div class="has-text-primary has-text-weight-bold has-text-left is-flex-grow-1 mr-5">
    {admin.full_name}
    <a href="{reverse('members:detail', args=[admin.id])}" aria-label="{_('profile')}">
      {icon("member-link")}
    </a>
  </div>
   {self.get_remove_text(room, admin, is_admin=True)}
</div>""",
            html=True,
        )


class PrivateChatRoomTests(PrivateChatRoomTestsMixin, MemberTestCase):
    def test_create_chat_room(self):
        """Tests creating a private chat room."""
        room_name = "a clean private room"
        slug = slugify(room_name)
        self.assertFalse(ChatRoom.objects.filter(slug=slug).exists())
        self.do_check_private_chat_room(room_name)
        # try a second time with the exact same name
        # the way it is coded, this will redirect to the existing room and create an error
        self.do_check_private_chat_room(room_name)
        # now, try with a direct creation, and check it raises a ValidationError
        with self.assertRaises(ValidationError):
            PrivateChatRoom.objects.create(name=room_name)
        with self.assertRaises(ValidationError):
            ChatRoom.objects.create(name=room_name)
        # and finally, try with a different room name but which has the same slug
        new_room_name = "#" + room_name + "!"
        new_slug = slugify(new_room_name)
        self.assertEqual(new_slug, slug)
        url = (
            reverse("chat:new_private_room") + "?" + urlencode({"name": new_room_name})
        )
        response = self.client.get(url, follow=True)
        # self.print_response(response)
        self.assertContainsMessage(
            response,
            "error",
            _(
                "Another room with a similar name already exists ('%(similar_room_name)s'). "
                "Please choose a different name."
            )
            % {"similar_room_name": room_name},
        )
        PrivateChatRoom.objects.all().delete()

    def test_list_private_rooms(self):
        """Tests listing private chat rooms."""
        rooms = []
        for i in range(5):
            name = "Private Chat Room #%i" % i
            url = reverse("chat:new_private_room") + "?" + urlencode({"name": name})
            response = self.client.get(url, follow=True)
            rooms.append(PrivateChatRoom.objects.get(name=name))
        ChatMessage.objects.create(
            room=rooms[0], content="a message", member=self.member
        )
        response = self.client.get(reverse("chat:private_chat_rooms"))
        # self.print_response(response)
        for i in range(5):
            self.check_private_chat_room_list(response, rooms[i], 1 if i == 0 else 0, 1)
        PrivateChatRoom.objects.all().delete()


class TestPrivateMembersAndAdmins(PrivateChatRoomTestsMixin, MemberTestCase):
    def setUp(self):
        super().setUp()
        # first create 5 active members
        for i in range(5):
            self.create_member(is_active=True)
        # then create a private room
        self.room = self.do_check_private_chat_room("a clean new private room")

    def tearDown(self):
        PrivateChatRoom.objects.all().delete()
        super().tearDown()

    def test_list_private_members(self):
        """Tests listing private chat room members."""
        # check creator of the private room was automatically added in the room members and admins
        self.assertIn(self.member, self.room.followers.all())
        self.assertIn(self.member, self.room.admins.all())
        # then add created members to the private room
        for member in self.created_members:
            response = self.client.post(
                reverse("chat:add_member_to_private_room", args=[self.room.slug]),
                {"member-id": member.id},
                follow=True,
            )
            back_to_room = _("Back to room")
            self.assertContains(
                response,
                f"""
<div class="buttons has-addons is-rounded ml-auto">
  <a class="button" title="{back_to_room}" href="{reverse('chat:private_room', args=[self.room.slug])}">
    {icon('back')}
    <span class="is-hidden-mobile">{back_to_room}</span>
  </a>
  {self.get_leave_text(self.room)}
</div>""",
                html=True,
            )
            # remove csrf token before checking
            content = response.content.decode("utf-8")
            cleaned_content = re.sub(
                r'<input type="hidden" name="csrfmiddlewaretoken" value="[^"]+">',
                "",
                content,
            )
            # print(cleaned_content)
            self.assertInHTML(
                f"""
<form id="add-member-form" method="post" action="{reverse('chat:add_member_to_private_room', args=[self.room.slug])}">
  <select id="member-select" name="member-id" style="width: 300px;"></select>
  <button class="button" type="submit" disabled="true" id="add-member-button">
    {icon("new-member")} {_("Add member to the room")}
  </button>
</form>""",
                cleaned_content,
            )
        # then list the members
        response = self.client.get(
            reverse("chat:private_room_members", args=[self.room.slug]), follow=True
        )
        # self.print_response(response)
        for member in (*self.created_members, self.member):
            self.check_private_members_list(response, self.room, member)
        # then delete some members and remove some others from the list
        self.created_members[0].delete()
        response = self.client.post(
            reverse(
                "chat:remove_member_from_private_room",
                args=[self.room.slug, self.created_members[1].id],
            ),
            follow=True,
        )
        # self.print_response(response)
        # then list the members again (this is the default redirection)
        self.assertTemplateUsed(response, "chat/private/room_members.html")
        self.assertNotContains(response, self.created_members[0].full_name)
        self.assertContainsMessage(
            response,
            "success",
            _("%s has been removed from the room") % self.created_members[1].full_name,
        )
        for member in (self.member, *self.created_members):
            self.check_private_members_list(response, self.room, self.member)
        del self.created_members[0]

    def test_list_private_admins(self):
        """Tests listing private chat room admins."""
        # try adding as an admin a user who is not a member of the room, should fail
        response = self.client.post(
            reverse("chat:add_admin_to_private_room", args=[self.room.slug]),
            {"member-id": self.created_members[0].id},
            follow=True,
        )
        self.assertNotIn(self.created_members[0], self.room.admins.all())
        self.assertContainsMessage(
            response, "error", _("Only members of this private room can become admins")
        )
        # then add created members to the private room
        for member in self.created_members:
            response = self.client.post(
                reverse("chat:add_member_to_private_room", args=[self.room.slug]),
                {"member-id": member.id},
                follow=True,
            )
            back_to_room = _("Back to room")
            self.assertContains(
                response,
                f"""
<div class="buttons has-addons is-rounded ml-auto">
  <a class="button" title="{back_to_room}" href="{reverse('chat:private_room', args=[self.room.slug])}">
    {icon('back')}
    <span class="is-hidden-mobile">{back_to_room}</span>
  </a>
  {self.get_leave_text(self.room)}
</div>""",
                html=True,
            )
            # remove csrf token before checking
            content = response.content.decode("utf-8")
            cleaned_content = re.sub(
                r'<input type="hidden" name="csrfmiddlewaretoken" value="[^"]+">',
                "",
                content,
            )
            # print(cleaned_content)
            self.assertInHTML(
                f"""
<form id="add-member-form" method="post" action="{reverse('chat:add_member_to_private_room', args=[self.room.slug])}">
  <select id="member-select" name="member-id" style="width: 300px;"></select>
  <button class="button" type="submit" disabled="true" id="add-member-button">
    {icon("new-member")}{_("Add member to the room")}
  </button>
</form>""",
                cleaned_content,
            )
        # now, select a random member
        second_member = random.choice(self.created_members)
        # then list the members
        response = self.client.get(
            reverse("chat:private_room_admins", args=[self.room.slug]), follow=True
        )
        # self.print_response(response)
        # only self.member and not second_member should be in the list
        self.check_private_admins_list(response, self.room, self.member)
        self.assertNotContains(response, second_member.full_name)

        # now, add a random member to self.room admins
        self.room.admins.add(second_member)
        self.room.save()
        self.assertEqual(self.room.admins.count(), 2)
        self.assertIn(second_member, self.room.admins.all())
        # and retest
        response = self.client.get(
            reverse("chat:private_room_admins", args=[self.room.slug]), follow=True
        )
        # self.print_response(response)
        for admin in [self.member, second_member]:
            self.check_private_admins_list(response, self.room, admin)
        for member in [
            member for member in self.created_members if member != second_member
        ]:
            self.assertNotContains(response, member.full_name)

    def test_remove_member_from_private_room(self):
        self.assertEqual(self.room.followers.count(), 1)
        first_member = self.room.followers.first()
        self.assertEqual(first_member, self.member)
        response = self.client.get(
            reverse(
                "chat:remove_member_from_private_room",
                args=[self.room.slug, first_member.id],
            ),
            follow=True,
        )
        self.assertContainsMessage(
            response,
            "error",
            _(
                "This member is the only one in this private room. "
                "Please add another one before removing this one."
            ),
        )
        # now, add a random member to self.room
        second_member = random.choice(self.created_members)
        self.room.followers.add(second_member)
        self.room.save()
        self.assertEqual(self.room.followers.count(), 2)
        # and retest
        response = self.client.get(
            reverse(
                "chat:remove_member_from_private_room",
                args=[self.room.slug, second_member.id],
            ),
            follow=True,
        )
        # self.print_response(response)
        self.assertContainsMessage(
            response,
            "success",
            _("%s has been removed from the room") % second_member.full_name,
        )
        self.assertEqual(PrivateChatRoom.objects.filter(name=self.room.name).count(), 1)

    def test_leave_private_room(self):
        # only one member and one admin and both are the same: self.member = connected user
        self.assertEqual(self.room.followers.count(), 1)
        self.assertEqual(self.room.admins.count(), 1)
        first_member = self.room.followers.first()
        self.assertEqual(first_member, self.member)
        from django.contrib.auth import get_user

        auth_member = get_user(self.client)
        self.assertEqual(first_member, auth_member)
        self.assertEqual(first_member, self.room.admins.first())

        response = self.client.get(
            reverse("chat:leave_private_room", args=[self.room.slug]), follow=True
        )
        # self.print_response(response)
        self.assertContainsMessage(
            response,
            "error",
            _(
                "You are the only member in this private room. "
                "Please add another one before removing yourself."
            ),
        )
        # now, add a random member to self.room
        second_member = random.choice(self.created_members)
        self.room.followers.add(second_member)
        self.room.save()
        self.assertEqual(self.room.followers.count(), 2)
        # and retest
        response = self.client.get(
            reverse("chat:leave_private_room", args=[self.room.slug]), follow=True
        )
        self.assertContainsMessage(
            response,
            "error",
            _(
                "You are the only admin in this private room. "
                "If you leave the room, no one will be left. "
                "Please add another admin from the members before you remove yourself."
            ),
        )
        # so add member as admin
        self.room.admins.add(second_member)
        self.room.save()
        # and retest
        response = self.client.get(
            reverse("chat:leave_private_room", args=[self.room.slug]), follow=True
        )
        # self.print_response(response)
        self.assertContainsMessage(response, "success", _("You have left the room"))
        self.assertEqual(PrivateChatRoom.objects.filter(name=self.room.name).count(), 1)

    def test_permissions(self):
        """Tests permissions for private chat rooms."""
        # create a second room as self.member
        second_room = self.do_check_private_chat_room("a second room")
        # login as someone who didn't create the rooms
        member = random.choice(self.created_members)
        self.client.login(username=member.username, password=member.password)
        response = self.client.get(reverse("chat:private_chat_rooms"), follow=True)
        self.assertTemplateUsed(response, "chat/chat_rooms.html")
        # none of the rooms should be visible
        self.assertNotContains(response, self.room.name)
        self.assertNotContains(response, second_room.name)
        # now, add the new member to self.room
        self.room.followers.add(member)
        self.room.save()
        response = self.client.get(reverse("chat:private_chat_rooms"), follow=True)
        # self.print_response(response)
        self.assertTemplateUsed(response, "chat/chat_rooms.html")
        # only self.room should be visible in the list of private rooms and its admin is self.member
        self.check_private_chat_room_list(response, self.room, 0, 2)
        self.assertNotContains(response, second_room.name)

        # check a non member can't access a private room
        response = self.client.get(
            reverse("chat:private_room", args=[second_room.slug]), follow=True
        )
        self.assertContainsMessage(
            response, "error", _("You are not a member of this private room")
        )
        self.assertTemplateUsed(response, "chat/chat_rooms.html")

        # check a member can access a private room
        response = self.client.get(
            reverse("chat:private_room", args=[self.room.slug]), follow=True
        )
        # self.print_response(response)
        self.assertTemplateUsed(response, "chat/room_detail.html")
        self.assertContains(
            response,
            f"""
<div class="mr-1 buttons has-addons is-rounded">
  {self.get_leave_text(self.room)}
  <a class="button" href="{reverse('chat:private_room_members', args=[self.room.slug])}">
    {icon("members")} <span>{_('Room Members')}</span>
  </a>
  <a class="button" href="{reverse('chat:private_room_admins', args=[self.room.slug])}">
    {icon("members")} <span>{_('Room Admins')}</span>
  </a>
</div>""",
            html=True,
        )

        # check a non admin can't add a member to a private room
        response = self.client.post(
            reverse("chat:add_member_to_private_room", args=[self.room.slug]),
            {"admin-id": self.member.id},
            follow=True,
        )
        self.assertContainsMessage(
            response, "error", _("You are not an admin of this private room")
        )
        self.assertTemplateUsed(response, "chat/chat_rooms.html")
