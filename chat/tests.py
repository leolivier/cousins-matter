from urllib.parse import urlencode

from django.conf import settings
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.test import tag
from django.contrib.auth import aget_user
from django.core import mail
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter

from cm_main.tests.tests_followers import TestFollowersMixin
from members.tests.tests_member_base import MemberTestCase
from .models import ChatMessage, ChatRoom
from .routing import websocket_urlpatterns


@sync_to_async
def astr(obj):
  return str(obj)


class ChatRoomTests(MemberTestCase):
  def do_check_chat_room(self, room_name, slug):
    url = reverse('chat:new_room') + '?' + urlencode({'name': room_name})
    response = self.client.get(url, follow=True)
    # self.print_response(response)
    # should be redirected to room detail
    self.assertTemplateUsed(response, 'chat/room_detail.html')
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, f'<span id="show-room-name">{room_name}</span>', html=True)
    follow = _('Follow')
    self.assertContains(response, f'''
<a class="button " href="{reverse("chat:toggle_follow", args=[slug])}"
   aria-label="{follow}" title="{follow}">
  <span class="icon is-large">
    <i class="mdi mdi-24px mdi-link-variant" aria-hidden="true"></i>
  </span>
  <span>{follow}</span>
</a>''', html=True)
    rooms = ChatRoom.objects.filter(slug=slug)
    self.assertEqual(rooms.count(), 1)
    return rooms.first()

  def test_create_chat_room(self):
    room_name = 'a clean room'
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
    new_room_name = '#'+room_name+'!'
    new_slug = slugify(new_room_name)
    self.assertEqual(new_slug, slug)
    url = reverse('chat:new_room') + '?' + urlencode({'name': new_room_name})
    response = self.client.get(url, follow=True)
    # self.print_response(response)
    self.assertContainsMessage(response, 'error',
                               _(f"Another room with a similar name already exists ('{room_name}'). "
                                 "Please choose a different name."))
    ChatRoom.objects.all().delete()

  def test_list_rooms(self):
    rooms = [ChatRoom.objects.create(name='Chat Room #%i' % i) for i in range(5)]
    ChatMessage.objects.create(room=rooms[0], content='a message', member=self.member)
    response = self.client.get(reverse('chat:chat_rooms'))
    # self.print_response(response)
    nmsgs = 1
    nfollowers = 0
    follow = _('Follow')
    self.assertContains(response, f'''
<div class="panel-block is-flex is-flex-wrap-wrap is-align-items-flex-start">
  <div class="px-1">
    <figure class="image mini-avatar mr-2">
      <img class="is-rounded" src="{self.member.avatar_mini_url()}" alt="foobar">
    </figure>
  </div>
  <div class="has-text-primary has-text-weight-bold has-text-right mr-5">
    {self.member.get_full_name()}
    <a href="{reverse("members:detail", kwargs={'pk': self.member.id})}" aria-label="profil">
      <span class="icon is-large">
        <i class="mdi mdi-24px mdi-open-in-new" aria-hidden="true"></i>
      </span>
    </a>
    <br>
    <span class="tag mr-3">{_(f"{nmsgs} message")}</span>
    <span class="tag ">{_(f'{nfollowers} follower')}</span>
  </div>
  <div class="is-flex-grow-1">
    <a class="title is-size-6" href="{reverse('chat:room', args=[rooms[0].slug])}">{rooms[0].name}</a>
  </div>
  <div class="mr-1">
    <a class="button is-pulled-right" href="{reverse('chat:toggle_follow', args=[rooms[0].slug])}"
      aria-label="{follow}" title="{follow}">
      <span class="icon is-large">
        <i class="mdi mdi-24px mdi-link-variant" aria-hidden="true"></i>
      </span>
      <span class="is-hidden-mobile">{follow}</span>
    </a>
  </div>
</div>''', html=True)
    nmsgs = 0
    for i in range(1, 5):
      self.assertContains(response, f'''
<div class="panel-block is-flex is-flex-wrap-wrap is-align-items-flex-start">
  <div class="px-1">
    <figure class="image mini-avatar mr-2">
      <img class="is-rounded" src="{settings.DEFAULT_AVATAR_URL}">
    </figure>
  </div>
  <div class="has-text-primary has-text-weight-bold has-text-right mr-5">
    {_("No author yet")}
    <span class="icon has-text-link is-large">
      <i class="mdi mdi-24px mdi-chat" aria-hidden="true"></i>
    </span>
    <br>
    <span class="tag mr-3">{_(f"{nmsgs} message")}</span>
    <span class="tag ">{_(f'{nfollowers} follower')}</span>
  </div>
  <div class="is-flex-grow-1">
    <a class="title is-size-6" href="{reverse('chat:room', args=[rooms[i].slug])}">{rooms[i].name}</a>
  </div>
  <div class="mr-1">
    <a class="button is-pulled-right" href="{reverse('chat:toggle_follow', args=[rooms[i].slug])}"
      aria-label="{follow}" title="{follow}">
      <span class="icon is-large">
       <i class="mdi mdi-24px mdi-link-variant" aria-hidden="true"></i>
      </span>
      <span class="is-hidden-mobile">{follow}</span>
    </a>
  </div>
</div>''', html=True)
    ChatRoom.objects.all().delete()


class ChatMessageSenderMixin():
  async def _send_msg(self, room_slug, data, disconnect):
    application = URLRouter(websocket_urlpatterns)
    communicator = WebsocketCommunicator(application, f"/chat/{room_slug}")
    connected, subprotocol = await communicator.connect()
    self.assertTrue(connected)
    # Test sending data as text
    await communicator.send_json_to(data)
    if disconnect:
      await communicator.disconnect()
    else:
      return communicator

  async def send_chat_message(self, msg, room_slug, disconnect=True):
    # sender is the currently connected user
    sender = await aget_user(self.client)
    data = {
      'action': 'create_chat_message',
      'args': {
        'message': msg,
        'member': sender.id,
        'username': sender.username,
        'room': room_slug,
      }
    }
    return await self._send_msg(room_slug, data, disconnect)

  async def send_delete_message(self, room_slug, msgid):
    data = {
      'action': 'delete_chat_message',
      'args': {
        'msgid': msgid
      }
    }
    return await self._send_msg(room_slug, data, disconnect=True)

  def setUp(self):
    super().setUp()
    self.room_name = 'test messages #1'
    self.slug = slugify(self.room_name)
    self.room = ChatRoom.objects.create(name=self.room_name)

  def tearDown(self):
    self.room.delete()
    self.room = None
    super().tearDown()


@tag("needs-redis")
class ChatMessageTests(ChatMessageSenderMixin, MemberTestCase):
  async def test_chat_consumer(self):
    msg = 'this is my message to the world!'
    communicator = await self.send_chat_message(msg, self.slug, disconnect=False)
    response = await communicator.receive_json_from()
    # print(response)
    self.assertTrue('args' in response)
    self.assertEqual(response['args']['message'], msg)
    self.assertEqual(response['args']['username'], self.member.username)
    message = await ChatMessage.objects.filter(room=self.room).afirst()
    self.assertIsNotNone(msg)
    self.assertEqual(response['args']['message'], message.content)
    self.assertEqual(self.member.id, message.member_id)
    # Close communication
    await communicator.disconnect()

    # now, delete the message
    await self.send_delete_message(self.slug, message.id)
    self.assertEqual(await ChatMessage.objects.acount(), 0)


@tag("needs-redis")
class ChatRoomFollowerTests(TestFollowersMixin, ChatMessageSenderMixin, MemberTestCase):

  @sync_to_async
  def acreate_member_and_login(self):
    return self.create_member_and_login()

  @sync_to_async
  def apost(self, url, *args, **kwargs):
    return self.client.post(url, *args, **kwargs)

  @sync_to_async
  def alogin_as(self, member):
    return self.login_as(member)

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

    # login back as self.member
    # await self.alogin_as(self.member)
