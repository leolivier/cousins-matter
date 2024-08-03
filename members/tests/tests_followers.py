from django.test import tag
from django.urls import reverse
from django.core import mail
from asgiref.sync import sync_to_async
from chat.models import ChatMessage, ChatRoom
from chat.tests.tests_mixin import ChatMessageSenderMixin
from cm_main.tests import get_absolute_url
from cm_main.tests.tests_followers import TestFollowersMixin
from forum.models import Message, Post
from .tests_member_base import MemberTestCase


@sync_to_async
def astr(obj):
  return str(obj)


class TestMemberFollowersMixin(TestFollowersMixin):
  def do_test_toggle_follow_member(self):
    follower = self.member
    followed = self.create_member(is_active=True)
    # follower follows followed
    url = reverse("members:toggle_follow", args=[followed.id])
    response = self.client.post(url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(followed.followers.first(), follower)
    return followed

  def do_test_toggle_unfollow_member(self, followed):
    # test unfollow
    self.login()  # login as follower (ie self.member)
    url = reverse("members:toggle_follow", args=[followed.id])
    response = self.client.post(url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(followed.followers.count(), 0)


class TestMemberFollower(TestMemberFollowersMixin, ChatMessageSenderMixin, MemberTestCase):

  def test_follow_member(self):
    follower = self.member
    followed = self.do_test_toggle_follow_member()
    followed_url = get_absolute_url(reverse("members:detail", args=[followed.id]))
    # now check the email to the owner to inform about the new follower
    self.check_new_follower_email(
      follower=follower,
      owner=followed,
      followed_object=followed,
      followed_url=followed_url)

    # now, followed will create a post
    self.login_as(followed)
    url = reverse("forum:create")
    post_title = 'a post to be followed'
    post_content = 'a content of the new post'
    response = self.client.post(url, {'title': post_title, 'content': post_content}, follow=True)
    self.assertEqual(response.status_code, 200)
    # self.print_response(response)
    post = Post.objects.get(title=post_title)
    post_url = reverse('forum:display', args=[post.id])
    self.assertRedirects(response, post_url)

    # now check the email to the follower to inform about the new post
    self.check_new_content_email(
      follower=follower,
      sender=None,
      owner=followed,
      followed_url=get_absolute_url(post_url),
      followed_object=post,
      created_object=post,
      created_content=post_title)

    # now, followed will reply to his own post
    url = reverse("forum:reply", args=[post.id])
    reply_msg_content = 'a reply to be followed'
    response = self.client.post(url, {'content': reply_msg_content}, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertRedirects(response, reverse('forum:display', args=[post.id]))

    message = Message.objects.get(post=post, content=reply_msg_content)
    self.assertEqual(message.author, followed)
    # now check the email to the follower to inform about the new reply
    self.check_new_content_email(
      follower=follower,
      sender=followed,
      owner=followed,
      followed_url=get_absolute_url(post_url),
      followed_object=post,
      created_object=message,
      created_content=reply_msg_content)

    # test unfollow
    self.do_test_toggle_unfollow_member(followed)


@tag("needs-redis")
class TestChatWithMemberFollower(TestMemberFollowersMixin, ChatMessageSenderMixin, MemberTestCase):
  # def tearDown(self):
  #   ChatMessageSenderMixin.tearDown(self)
  #   super(MemberTestCase, self).tearDown()

  @sync_to_async
  def ado_test_toggle_follow_member(self):
    return self.do_test_toggle_follow_member()

  @sync_to_async
  def ado_test_toggle_unfollow_member(self, followed):
    return self.do_test_toggle_unfollow_member(followed)

  @sync_to_async
  def aget(self, url, *args, **kwargs):
    return self.client.get(url, *args, **kwargs)

  @sync_to_async
  def alogin_as(self, member):
    return self.login_as(member)

  @sync_to_async
  def alogin(self):
    return self.login()

  async def test_follow_room(self):
    """test room follow in the context of member follow"""
    follower = self.member
    followed = await self.ado_test_toggle_follow_member()
    # reseet the mail outbox
    mail.outbox = []

    # first, followed creates a chat room
    await self.alogin_as(followed)
    room_name = 'a room to be followed'
    response = await self.aget(reverse('chat:new_room'), {'name': room_name})
    self.assertEqual(response.status_code, 302)
    room = await ChatRoom.objects.aget(name=room_name)
    room_url = get_absolute_url(reverse('chat:room', args=[room.slug]))
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
    msg = 'this is the first message on the room so I become the owner!'
    await self.send_chat_message(msg, room_slug=room.slug)
    message = await ChatMessage.objects.aget(room=room, content=msg)
    self.check_new_content_email(
      follower=follower,
      sender=followed,
      owner=followed,
      followed_url=room_url,
      followed_object=room,
      created_object=message,
      created_content=await astr(message),
    )
    # await room.adelete()

    # now, let follower create a room and it's 1rst message and let the
    # followed reply to it, and check the email to the follower
    await self.alogin()  # login as follower ie self.member

    room_name = 'a new room created by follower'
    response = await self.aget(reverse('chat:new_room'), {'name': room_name})
    self.assertEqual(response.status_code, 302)
    room = await ChatRoom.objects.aget(name=room_name)
    room_url = get_absolute_url(reverse('chat:room', args=[room.slug]))
    first_msg = "a 1rst msg in the followed's room"
    await self.send_chat_message(first_msg, room_slug=room.slug)

    # force reset the mail outbox.
    mail.outbox = []
    # now, followed will reply to the follower's message
    await self.alogin_as(followed)
    reply_msg = "a reply to be followed's room"
    await self.send_chat_message(reply_msg, room_slug=room.slug)

    message = await ChatMessage.objects.aget(room=room, content=reply_msg)
    self.check_new_content_email(
      follower=follower,
      sender=followed,
      owner=follower,
      followed_url=room_url,
      followed_object=room,
      created_object=message,
      created_content=await astr(message),
    )
    # await room.adelete()

    # test unfollow
    await self.ado_test_toggle_unfollow_member(followed)
