from asgiref.sync import sync_to_async, async_to_sync
from django.urls import reverse
from django.test import tag
from django.core import mail

from core.utils import get_test_absolute_url
from core.tests.tests_followers import TestFollowersMixin
from members.tests.tests_member_base import AsyncMemberTestCase, TransactionMemberTestCase
from ..models import ChatMessage, ChatRoom
from .tests_mixin import ChatMessageSenderMixin
from core.tests.test_django_q import async_django_q_sync_class


@tag("needs-redis", "followers")
@async_django_q_sync_class
class ChatRoomFollowerTests(ChatMessageSenderMixin, TestFollowersMixin, AsyncMemberTestCase):
  async def test_follow_room(self):
    """Tests following a chat room and verifying email notifications to followers."""
    # we should start with zero followers
    self.assertEqual(await self.room.followers.acount(), 0)

    # create a new member and login, he will send a first
    # message on the room and become the owner
    new_poster = await self.acreate_member(is_active=True)
    await self.async_client.alogin(username=new_poster.username, password=new_poster.password)
    msg = "this is the first message on the room so I am the owner!"
    await self.send_chat_message(msg, self.slug, sender=new_poster)

    # make sure the outbox is empty
    mail.outbox = []

    # create another new member and login, he will be the follower
    follower = await self.acreate_member(is_active=True)
    await self.async_client.alogin(username=follower.username, password=follower.password)
    response = await self.async_client.post(reverse("chat:toggle_follow", args=[self.slug]))
    self.assertEqual(response.status_code, 302)
    # now we should have one follower which is the new member
    await self.room.arefresh_from_db()
    self.assertEqual(await self.room.followers.acount(), 1)
    # and the first follower should be the new member
    self.assertEqual(await self.room.followers.afirst(), follower)

    # now log again as new_poster and send another message on the room
    await self.async_client.alogin(username=new_poster.username, password=new_poster.password)
    msg = "this is a message to my followers!"
    await self.send_chat_message(msg, self.slug, sender=new_poster)

    # get the message
    message = await ChatMessage.objects.aget(room=self.room, content=msg)
    await sync_to_async(self.check_followers_emails)(
      follower=follower,
      sender=new_poster,
      owner=new_poster,
      url=reverse("chat:room", args=[self.slug]),
      followed_object=self.room,
      created_object=message,
      created_content=await sync_to_async(str)(message),
    )

    # login back as follower
    await self.async_client.alogin(username=follower.username, password=follower.password)
    # now unfollow the room
    await self.async_client.post(reverse("chat:toggle_follow", args=[self.slug]))
    self.assertEqual(await self.room.followers.acount(), 0)


@tag("needs-redis", "followers")
class TestChatWithMemberFollower(ChatMessageSenderMixin, TestFollowersMixin, TransactionMemberTestCase):
  def test_follow_room(self):
    """Tests chat room following in the context of one member following another."""
    # setup follower and followed
    follower = self.member
    followed = self.create_member(is_active=True)
    followed.followers.add(follower)
    # reset the mail outbox
    mail.outbox = []

    # first, followed creates a chat room
    self.client.login(username=followed.username, password=followed.password)
    room_name = "a room to be followed"
    response = self.client.post(reverse("chat:new_room"), {"name": room_name})
    self.assertEqual(response.status_code, 302)
    room = ChatRoom.objects.get(name=room_name)
    room_url = get_test_absolute_url(reverse("chat:room", args=[room.slug]))
    # now check the email to the follower to inform about the new room
    self.check_new_content_email(
      follower=follower,
      sender=None,
      owner=followed,
      followed_url=room_url,
      followed_object=room,
      created_object=room,
      created_content=room_name,
    )

    # now, followed will create a message on the room
    msg = "this is the first message on the room so I become the owner!"
    async_to_sync(self.send_chat_message)(msg, room_slug=room.slug, sender=followed)
    message = ChatMessage.objects.get(room=room, content=msg)
    self.assertIsNotNone(message)
    self.check_new_content_email(
      follower=follower,
      sender=followed,
      owner=followed,
      followed_url=room_url,
      followed_object=room,
      created_object=message,
      created_content=str(message),
    )
    # await room.adelete()

    # now, let someone else (the superuser) create a room and it's 1rst message and let the
    # followed reply to it, and check the email to the follower
    self.client.login(username=self.superuser.username, password=self.superuser.password)

    room_name = "a new room created by superuser"
    response = self.client.post(reverse("chat:new_room"), {"name": room_name}, follow=True)
    self.assertEqual(response.status_code, 200)
    room = ChatRoom.objects.get(name=room_name)
    room_url = get_test_absolute_url(reverse("chat:room", args=[room.slug]))
    first_msg = "a 1rst msg in the superuser's room"
    async_to_sync(self.send_chat_message)(first_msg, room_slug=room.slug, sender=self.superuser)

    # force reset the mail outbox.
    mail.outbox = []
    # now, followed will reply to the superuser's message
    self.client.login(username=followed.username, password=followed.password)
    reply_msg = "a reply to be superuser's message"
    async_to_sync(self.send_chat_message)(reply_msg, room_slug=room.slug, sender=followed)
    print("follower email", follower.email)
    print("followed email", followed.email)
    print("superuser email", self.superuser.email)
    message = ChatMessage.objects.get(room=room, content=reply_msg)
    self.check_new_content_email(
      follower=follower,
      sender=followed,
      owner=self.superuser,
      followed_url=room_url,
      followed_object=room,
      created_object=message,
      created_content=str(message),
    )
    room.delete()
