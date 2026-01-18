from asgiref.sync import sync_to_async
from django.urls import reverse
from django.test import tag
from django.core import mail

from cm_main.utils import get_test_absolute_url
from cm_main.tests.tests_followers import TestFollowersMixin
from members.tests.tests_member_base import AsyncMemberTestCase
from ..models import ChatMessage, ChatRoom
from .tests_mixin import ChatMessageSenderMixin
from cm_main.tests.test_django_q import async_django_q_sync_class


@tag("needs-redis")
@async_django_q_sync_class
class ChatRoomFollowerTests(ChatMessageSenderMixin, TestFollowersMixin, AsyncMemberTestCase):
  async def test_follow_room(self):
    "Tests following a chat room."
    # we should start with zero followers
    self.assertEqual(await self.room.followers.acount(), 0)

    # create a new member and login, he will send a first
    # message on the room and become the owner
    new_poster = await self.acreate_member(is_active=True)
    await self.async_client.alogin(username=new_poster.username, password=new_poster.password)
    msg = "this is the first message on the room si I am the owner!"
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


@tag("needs-redis")
@async_django_q_sync_class
class TestChatWithMemberFollower(ChatMessageSenderMixin, TestFollowersMixin, AsyncMemberTestCase):
  async def test_follow_room(self):
    """test room follow in the context of member follow"""
    # setup follower and followed
    follower = self.member
    followed = await self.acreate_member(is_active=True)
    await followed.followers.aadd(follower)
    # reset the mail outbox
    mail.outbox = []

    # first, followed creates a chat room
    await self.async_client.alogin(username=followed.username, password=followed.password)
    room_name = "a room to be followed"
    response = await self.async_client.get(reverse("chat:new_room"), {"name": room_name})
    self.assertEqual(response.status_code, 302)
    room = await ChatRoom.objects.aget(name=room_name)
    room_url = get_test_absolute_url(reverse("chat:room", args=[room.slug]))
    # now check the email to the follower to inform about the new room
    await sync_to_async(self.check_new_content_email, thread_sensitive=False)(
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
    await self.send_chat_message(msg, room_slug=room.slug, sender=followed)
    message = await ChatMessage.objects.aget(room=room, content=msg)
    self.assertIsNotNone(message)
    await sync_to_async(self.check_new_content_email, thread_sensitive=False)(
      follower=follower,
      sender=followed,
      owner=followed,
      followed_url=room_url,
      followed_object=room,
      created_object=message,
      created_content=await sync_to_async(str)(message),
    )
    # await room.adelete()

    # now, let follower create a room and it's 1rst message and let the
    # followed reply to it, and check the email to the follower
    await self.async_client.alogin(username=follower.username, password=follower.password)

    room_name = "a new room created by follower"
    response = await self.async_client.get(reverse("chat:new_room"), {"name": room_name})
    self.assertEqual(response.status_code, 302)
    room = await ChatRoom.objects.aget(name=room_name)
    room_url = get_test_absolute_url(reverse("chat:room", args=[room.slug]))
    first_msg = "a 1rst msg in the followed's room"
    await self.send_chat_message(first_msg, room_slug=room.slug, sender=follower)

    # force reset the mail outbox.
    mail.outbox = []
    # now, followed will reply to the follower's message
    await self.async_client.alogin(username=followed.username, password=followed.password)
    reply_msg = "a reply to be followed's room"
    await self.send_chat_message(reply_msg, room_slug=room.slug, sender=followed)

    message = await ChatMessage.objects.aget(room=room, content=reply_msg)
    await sync_to_async(self.check_new_content_email, thread_sensitive=False)(
      follower=follower,
      sender=followed,
      owner=follower,
      followed_url=room_url,
      followed_object=room,
      created_object=message,
      created_content=await sync_to_async(str)(message),
    )
    # await room.adelete()
