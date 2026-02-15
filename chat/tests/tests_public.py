from urllib.parse import urlencode

from django.conf import settings
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import gettext as _, ngettext
from django.core.exceptions import ValidationError
from django.test import tag
from django.utils.formats import date_format
from django.utils import timezone

from chat.tests.tests_mixin import ChatMessageSenderMixin
from members.tests.tests_member_base import MemberTestCase, AsyncMemberTestCase
from cm_main.tests.test_django_q import async_django_q_sync_class
from ..models import ChatMessage, ChatRoom


class ChatRoomTests(MemberTestCase):
  def do_check_chat_room(self, room_name, slug):
    url = reverse("chat:new_room")
    response = self.client.post(url, {"name": room_name}, follow=True)
    # self.print_response(response)
    # should be redirected to room detail. if not, it means there was an error
    self.assertTemplateUsed(response, "chat/room_detail.html")
    self.assertContains(response, f'<div hx-target="this" hx-swap="outerHTML"><span>{room_name}</span></div>', html=True)
    follow = _("Follow")
    self.assertContains(
      response,
      f"""
<a class="button ml-auto mr-5" href="{reverse("chat:toggle_follow", args=[slug])}"
   aria-label="{follow}" title="{follow}">
  <span class="icon is-large">
    <i class="mdi mdi-24px mdi-link-variant" aria-hidden="true"></i>
  </span>
  <span>{follow}</span>
</a>""",
      html=True,
    )
    rooms = ChatRoom.objects.filter(slug=slug)
    self.assertEqual(rooms.count(), 1)
    return rooms.first()

  def test_create_chat_room(self):
    """Tests creating a public chat room."""
    room_name = "a clean room"
    slug = slugify(room_name)
    self.assertFalse(ChatRoom.objects.filter(slug=slug).exists())
    self.do_check_chat_room(room_name, slug)
    # try a second time with the exact same name
    # the way it is coded, this will redirect to the existing room and create an error
    self.do_check_chat_room(room_name, slug)
    # now, try with a direct creation, and check it raises a ValidationError
    with self.assertRaises(ValidationError):
      ChatRoom.objects.create(name=room_name)
    # and finally, try with a different room name but which has the same slug
    new_room_name = "#" + room_name + "!"
    new_slug = slugify(new_room_name)
    self.assertEqual(new_slug, slug)
    url = reverse("chat:new_room")
    response = self.client.post(url, {"name": new_room_name}, follow=True)
    # self.print_response(response)
    self.assertContainsMessage(
      response,
      "error",
      _("Another room with a similar name already exists ('%(similar_room_name)s'). Please choose a different name.")
      % {"similar_room_name": room_name},
    )
    ChatRoom.objects.all().delete()

  def test_list_rooms(self):
    """Tests listing public chat rooms."""
    rooms = [ChatRoom.objects.create(name="Chat Room #%i" % i) for i in range(5)]
    ChatMessage.objects.create(room=rooms[0], content="a message", member=self.member)
    response = self.client.get(reverse("chat:chat_rooms"))
    # self.print_response(response)
    nmsgs = ngettext("%(nmsgs)s message", "%(nmsgs)s messages", 1) % {"nmsgs": 1}
    nfollowers = ngettext("%(nfollowers)s follower", "%(nfollowers)s followers", 0) % {"nfollowers": 0}
    follow = _("Follow")
    profile = _("profile")
    self.assertContains(
      response,
      f"""
<div class="panel-block is-flex is-flex-wrap-wrap is-align-items-flex-start">
  <div class="panel-icon mini-avatar is-flex is-align-items-center is-justify-content-center is-flex-shrink-5 image">
    <img class="is-rounded" src="{self.member.avatar_mini_url}" alt="{self.member.username}">
  </div>
  <div class="is-flex-shrink-1 has-text-primary has-text-weight-bold mr-5">
    {self.member.full_name}
    <a href="{reverse("members:detail", kwargs={"pk": self.member.id})}" aria-label="{profile}">
      <span class="icon is-large"><i class="mdi mdi-24px mdi-open-in-new" aria-hidden="true"></i></span>
    </a>
    <br>
    <span class="tag mr-3">{nmsgs}</span>
    <span class="tag ">{nfollowers}</span>
  </div>
  <div class="is-flex-grow-1">
    <a class="title is-size-6" href="{reverse("chat:room", args=[rooms[0].slug])}">{rooms[0].name}</a>
  </div>
  <div class="mr-1">
    <a class="button is-pulled-right" href="{reverse("chat:toggle_follow", args=[rooms[0].slug])}"
      aria-label="{follow}" title="{follow}">
      <span class="icon is-large"><i class="mdi mdi-24px mdi-link-variant" aria-hidden="true"></i></span>
      <span class="is-hidden-mobile">{follow}</span>
    </a>
  </div>
</div>
""",
      html=True,
    )
    nmsgs = ngettext("%(nmsgs)s message", "%(nmsgs)s messages", 0) % {"nmsgs": 0}
    nobody = _("No author yet")
    for i in range(1, 5):
      self.assertContains(
        response,
        f"""
<div class="panel-block is-flex is-flex-wrap-wrap is-align-items-flex-start">
  <div class="panel-icon mini-avatar is-flex is-align-items-center is-justify-content-center is-flex-shrink-5 image">
      <img class="is-rounded" src="{settings.DEFAULT_AVATAR_URL}" alt="{nobody}">
  </div>
  <div class="is-flex-shrink-1 has-text-primary has-text-weight-bold mr-5">
    {nobody}
    <span class="icon has-text-link is-large"><i class="mdi mdi-24px mdi-chat" aria-hidden="true"></i></span>
    <br>
    <span class="tag mr-3">{nmsgs}</span>
    <span class="tag ">{nfollowers}</span>
  </div>
  <div class="is-flex-grow-1">
    <a class="title is-size-6" href="{reverse("chat:room", args=[rooms[i].slug])}">{rooms[i].name}</a>
  </div>
  <div class="mr-1">
    <a class="button is-pulled-right" href="{reverse("chat:toggle_follow", args=[rooms[i].slug])}"
      aria-label="{follow}" title="{follow}">
      <span class="icon is-large"><i class="mdi mdi-24px mdi-link-variant" aria-hidden="true"></i></span>
      <span class="is-hidden-mobile">{follow}</span>
    </a>
  </div>
</div>""",
        html=True,
      )
    ChatRoom.objects.all().delete()

  def test_edit_room(self):
    room = ChatRoom.objects.create(name="a room")
    url = reverse("chat:room-edit", args=[room.slug])
    response = self.client.get(url, HTTP_HX_REQUEST="true")
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "room_edit_form")

    # post a new name
    new_name = "a new name"
    response = self.client.put(
      url, urlencode({"room-name": new_name}), content_type="application/x-www-form-urlencoded", HTTP_HX_REQUEST="true"
    )
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response["HX-Redirect"], reverse("chat:room", args=[slugify(new_name)]))
    room.refresh_from_db()
    self.assertEqual(room.name, new_name)

  def test_delete_room(self):
    room = ChatRoom.objects.create(name="a room")
    url = reverse("chat:room-delete", args=[room.slug])
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "cm_main/common/confirm-delete-modal-htmx.html")
    response = self.client.post(url)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response["HX-Redirect"], reverse("chat:chat_rooms"))
    self.assertFalse(ChatRoom.objects.filter(id=room.id).exists())


@tag("needs-redis")
@async_django_q_sync_class
class ChatMessageTests(ChatMessageSenderMixin, AsyncMemberTestCase):
  async def test_chat_consumer(self):
    """Tests the chat consumer."""
    msg = "this is my message to the world!"
    communicator = await self.send_chat_message(msg, self.slug, disconnect=False, sender=self.member)
    response = await communicator.receive_json_from()
    self.assertIn("args", response)
    self.assertIn("rendered_message", response["args"])
    rendered_message = response["args"]["rendered_message"]
    self.assertIn(msg, rendered_message)
    now = timezone.localtime(timezone.now())
    self.assertIn(date_format(now, "DATE_FORMAT"), rendered_message)
    self.assertIn(date_format(now, "TIME_FORMAT"), rendered_message)
    self.assertNotIn(self.member.get_full_name(), rendered_message)  # because it is my message
    message = await ChatMessage.objects.filter(room=self.room).afirst()
    self.assertIsNotNone(message)
    self.assertIn(message.content, rendered_message)
    self.assertEqual(self.member.id, message.member_id)
    # Close communication
    await communicator.disconnect()

    # now, update the message and check it is updated
    new_msg = "this is my updated message to the world!"
    communicator = await self.send_updated_message(self.slug, message.id, new_msg, disconnect=False)
    response = await communicator.receive_json_from()

    self.assertIn("args", response)
    self.assertEqual(response["args"]["message"], new_msg)
    self.assertEqual(response["args"]["msgid"], message.id)
    await message.arefresh_from_db()
    self.assertEqual(message.content, new_msg)
    # Close communication
    await communicator.disconnect()

    # now, delete the message and check it is deleted
    await self.send_delete_message(self.slug, message.id)
    await message.arefresh_from_db()
    self.assertEqual(message.content, "**This message has been deleted**")

  async def test_chat_consumer_same_date(self):
    """Tests that the date is not displayed when 2 messages are sent on the same date."""
    msg1 = "this is my message to the world!"
    # Send first message
    communicator1 = await self.send_chat_message(msg1, self.slug, disconnect=False, sender=self.member)
    response1 = await communicator1.receive_json_from()
    rendered_message1 = response1["args"]["rendered_message"]

    # Check that date header IS present in first message (since it's the first one of the day/room)
    # The class for the date header paragraph
    date_header_class = "has-text-centered is-size-7 has-text-link mx-auto my-3"
    self.assertIn(date_header_class, rendered_message1)

    # Send second message
    msg2 = "this is my second message to the world!"
    communicator2 = await self.send_chat_message(msg2, self.slug, disconnect=False, sender=self.member)
    response2 = await communicator2.receive_json_from()
    rendered_message2 = response2["args"]["rendered_message"]

    # Check that date header is NOT present in second message
    self.assertNotIn(date_header_class, rendered_message2)

    await communicator1.disconnect()
    await communicator2.disconnect()

  async def test_chat_consumer_different_users(self):
    """Tests that the full name is displayed when a different user sends a message."""
    # 1. Send message as member 1
    msg1 = "this is my message to the world!"
    # We keep communicator1 open to receive the second and third message broadcast
    communicator1 = await self.send_chat_message(msg1, self.slug, disconnect=False, sender=self.member)
    response1 = await communicator1.receive_json_from()
    # consume the message on communicator1
    self.assertIn("rendered_message", response1["args"])

    # 2. Create member 2
    member2 = await self.acreate_member(username="member2", first_name="Member", last_name="Two")

    # 3. Send message as member 2
    msg2 = "this is my second message to the world!"
    communicator2 = await self.send_chat_message(msg2, self.slug, disconnect=False, sender=member2)

    # 4. Receive message on communicator1 (member1's view)
    response2_on_1 = await communicator1.receive_json_from()
    rendered_message = response2_on_1["args"]["rendered_message"]

    # 5. Verify member2's full name is in the rendered message
    # Since member1 != member2, member1 should see the name of member2
    self.assertIn(member2.get_full_name(), rendered_message)

    # 6. Send another message as member 2
    msg3 = "this is my third message to the world!"
    communicator3 = await self.send_chat_message(msg3, self.slug, disconnect=False, sender=member2)
    response3 = await communicator1.receive_json_from()
    rendered_message3 = response3["args"]["rendered_message"]

    # 7. Verify member2's full name is not in the rendered message
    # Since the sender is the same as the previous message, the full name should not be displayed
    self.assertNotIn(member2.get_full_name(), rendered_message3)

    await communicator1.disconnect()
    await communicator2.disconnect()
    await communicator3.disconnect()
