from django.urls import reverse
from django.test import tag
from django.core import mail

from cm_main.tests.tests_followers import TestFollowersMixin
from members.tests.tests_member_base import MemberTestCase
from ..models import ChatMessage
from .tests_mixin import ChatMessageSenderMixin, astr


@tag("needs-redis")
class ChatRoomFollowerTests(TestFollowersMixin, ChatMessageSenderMixin, MemberTestCase):

  async def test_follow_room(self):
    # we should start with zéro followers
    self.assertEqual(await self.room.followers.acount(), 0)

    # create a new member and login, he will send a first
    # message on the room and become the owner
    new_poster = await self.acreate_member_and_login()
    msg = 'this is the first message on the room si I am the owner!'
    await self.send_chat_message(msg, self.slug)

    # make sure the outbox is empty
    mail.outbox = []

    # create another new member and login, he will be the follower
    follower = await self.acreate_member_and_login()
    await self.apost(reverse('chat:toggle_follow', args=[self.slug]))
    # now we should have one follower which is the new member
    self.assertEqual(await self.room.followers.acount(), 1)
    # and the first follower should be the new member
    self.assertEqual(await self.room.followers.afirst(), follower)

    # now log again as new_poster and send another message on the room
    await self.alogin_as(new_poster)
    msg = 'this is a message to my followers!'
    await self.send_chat_message(msg, self.slug)

    # get the message
    message = await ChatMessage.objects.aget(room=self.room, content=msg)
    self.check_followers_emails(
      follower=follower,
      sender=new_poster,
      owner=new_poster,
      url=reverse('chat:room', args=[self.slug]),
      followed_object=self.room,
      created_object=await ChatMessage.objects.aget(room=self.room, content=msg),
      created_content=await astr(message),
    )

    # login back as follower
    await self.alogin_as(follower)
    # now unfollow the room
    await self.apost(reverse('chat:toggle_follow', args=[self.slug]))
    self.assertEqual(await self.room.followers.acount(), 0)
