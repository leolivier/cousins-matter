from urllib.parse import urlencode

from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.test import tag
from django.contrib.auth import get_user

from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter

from cm_main.tests import TestFollowersMixin
from members.tests.tests_member import MemberTestCase
from .models import ChatMessage, ChatRoom
from .routing import websocket_urlpatterns


class ChatRoomTests(MemberTestCase):
  def test_create_chat_room(self):
    room_name = 'a clean room'
    slug = slugify(room_name)
    self.assertFalse(ChatRoom.objects.filter(slug=slug).exists())
    response = self.client.get(reverse('chat:new_room') + '?' + urlencode({'name': room_name}), follow=True)
    self.assertTrue(response.status_code, 200)
    rooms = ChatRoom.objects.filter(slug=slug)
    self.assertEqual(rooms.count(), 1)
    response = self.client.get(reverse('chat:new_room') + '?' + urlencode({'name': room_name}), follow=True)
    rooms = ChatRoom.objects.filter(slug=slug)
    self.assertEqual(rooms.count(), 1, "Two rooms with the same slug created")
    with self.assertRaises(ValidationError):
      ChatRoom.objects.create(name=room_name)
    response = self.client.get(reverse('chat:new_room') + '?' + urlencode({'name': '#'+room_name+'!'}), follow=True)
    slug_name = room_name
    self.assertContainsMessage(response, 'error',
                               _(f"Another room with a similar name already exists ('{slug_name}'). "
                                 "Please choose a different name."))
    ChatRoom.objects.all().delete()

  def test_list_rooms(self):
    rooms = [ChatRoom.objects.create(name='Chat Room #%i' % i) for i in range(5)]
    ChatMessage.objects.create(room=rooms[0], content='a message', member=self.member)
    response = self.client.get(reverse('chat:chat'))
    # self.print_response(response)
    nmsgs = 1
    nfollowers = 0
    self.assertContains(response, f'''
<div class="panel-block">
  <figure class="image mini-avatar mr-2">
    <img class="is-rounded" src="{self.member.avatar_mini_url()}" alt="foobar">
  </figure>
  <p class="content">
    {_('Created by:')}<br>
    <span class="has-text-primary has-text-weight-bold has-text-right mr-5">
      {self.member.username}
      <a href="{reverse('members:detail', args=[self.member.id])}" aria-label="{_('profile')}">
        <span class="icon"><i class="mdi mdi-open-in-new"></i></span>
      </a>
      <br>
      <span class="tag mr-3">{_(f"{nmsgs} message")}</span>
      <span class="tag ">{_(f'{nfollowers} follower')}</span>
    </span>
  </p>
  <a class="title is-size-6" href="{reverse('chat:room', args=[rooms[0].slug])}">{rooms[0].name}</a>
  <a class="button ml-3 mr-3 is-pulled-right" href="{reverse('chat:toggle_follow', args=[rooms[0].slug])}"
    aria-label="{_('follow')}" title="{_('follow')}">
    <span class="icon is-large"><i class="mdi mdi-24px mdi-arrow-up-bold-hexagon-outline"></i></span>
  </a>
</div>''', html=True)
    nmsgs = 0
    for i in range(1, 5):
      self.assertContains(response, f'''
<div class="panel-block">
  <span class="panel-icon"><i class="mdi mdi-24px mdi-chat-outline" aria-hidden="true"></i></span>
  <a class="block" href="{reverse('chat:room', args=[rooms[i].slug])}">
    <span class="tag mr-3">{_(f"{nmsgs} message")}</span>
    <span class="title is-size-6">{rooms[i].name}</span>
  </a>
  <a class="button ml-3 mr-3 is-pulled-right" href="{reverse('chat:toggle_follow', args=[rooms[i].slug])}"
    aria-label="{_('follow')}" title="{_('follow')}">
    <span class="icon is-large"><i class="mdi mdi-24px mdi-arrow-up-bold-hexagon-outline"></i></span>
  </a>
</div>''', html=True)
    ChatRoom.objects.all().delete()


@tag("needs-redis")
class ChatMessageTestBase(MemberTestCase):
  def setUp(self):
    super().setUp()
    self.room_name = 'test messages #1'
    self.slug = slugify(self.room_name)
    self.room = ChatRoom.objects.create(name=self.room_name)

  def tearDown(self):
    self.room.delete()
    self.room = None
    super().tearDown()

  @sync_to_async
  def get_room_first_msg(self):
    return ChatMessage.objects.filter(room=self.room).first()

  @sync_to_async
  def check_msg_member(self, msg):
    self.assertEqual(self.member, msg.member)

  @sync_to_async
  def async_get_user(self):
    return get_user(self.client)

  async def send_chat_message(self, msg):
    # sender is the currently connected user
    sender = await self.async_get_user()
    data = {
      'message': msg,
      'member': sender.id,
      'username': sender.username,
      'room': self.slug,
    }
    application = URLRouter(websocket_urlpatterns)
    communicator = WebsocketCommunicator(application, f"/chat/{self.slug}")
    connected, subprotocol = await communicator.connect()
    self.assertTrue(connected)
    # Test sending data as text
    await communicator.send_json_to(data)
    return communicator


class ChatMessageTests(ChatMessageTestBase):
  async def test_chat_consumer(self):
    msg = 'this is my message to the world!'
    communicator = await self.send_chat_message(msg)
    response = await communicator.receive_json_from()
    # print(response)
    self.assertEqual(response['message'], msg)
    self.assertEqual(response['username'], self.member.username)
    message = await self.get_room_first_msg()
    self.assertIsNotNone(msg)
    self.assertEqual(response['message'], message.content)
    await self.check_msg_member(message)
    # Close
    await communicator.disconnect()


@tag("needs-redis")
class ChatRoomFollowerTests(TestFollowersMixin, ChatMessageTestBase):
  @sync_to_async
  def assertFollowersCountEqual(self, count):
    self.assertEqual(self.room.followers.count(), count)

  @sync_to_async
  def assertFirstFollowerIs(self, follower):
    self.assertEqual(self.room.followers.first(), follower)

  @sync_to_async
  def async_create_member_and_login(self):
    return self.create_member_and_login()

  @sync_to_async
  def async_post(self, url, *args, **kwargs):
    return self.client.post(url, *args, **kwargs)

  @sync_to_async
  def async_login_as(self, member):
    return self.login_as(member)

  @sync_to_async
  def async_get_message(self, content):
    return ChatMessage.objects.get(content=content)

  async def test_follow_room(self):
    # we should start with zéro followers
    await self.assertFollowersCountEqual(0)

    # now create a new member and login, he will send a first
    # message on the room and become the owner
    new_poster = await self.async_create_member_and_login()
    msg = 'this is the first message on the room si I am the owner!'
    communicator = await self.send_chat_message(msg)
    # Close communication
    await communicator.disconnect()

    # create another new member and login, he will be the follower
    follower = await self.async_create_member_and_login()
    await self.async_post(reverse('chat:toggle_follow', args=[self.slug]))
    # now we should have one follower which is the new member
    await self.assertFollowersCountEqual(1)
    await self.assertFirstFollowerIs(follower)

    # now log again as new_poster and send another message on the room
    await self.async_login_as(new_poster)
    msg = 'this is a message to my followers!'
    communicator = await self.send_chat_message(msg)
    # Close communication
    await communicator.disconnect()

    self.check_followers_emails(
      follower=follower,
      sender=new_poster,
      owner=new_poster,
      url=reverse('chat:room', args=[self.slug]),
      followed_object=self.room,
      created_object=await self.async_get_message(msg),
      created_content=msg,
    )

    # login back as follower
    await self.async_login_as(follower)
    # now unfollow the room
    await self.async_post(reverse('chat:toggle_follow', args=[self.slug]))
    await self.assertFollowersCountEqual(0)

    # login back as self.member
    # await self.async_login_as(self.member)
