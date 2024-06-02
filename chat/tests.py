from urllib.parse import urlencode
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from members.tests.tests_member import MemberTestCase
from channels.routing import URLRouter
from django.test import tag
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
                                _(f"Another room with a similar name already exists ('{slug_name}'). Please choose a different name."))  # noqa E501
    ChatRoom.objects.all().delete()

  def test_list_rooms(self):
    rooms = [ChatRoom.objects.create(name='Chat Room #%i' % i) for i in range(5)]
    response = self.client.get(reverse('chat:chat'))
    for i in range(5):
      self.assertContains(response, f'''
  <a class="panel-block" href="{reverse('chat:room', args=[rooms[i].slug])}">
    <span class="panel-icon">
      <i class="mdi mdi-24px mdi-chat-outline" aria-hidden="true"></i>
    </span>
    {rooms[i].name}
  </a>''', html=True)
    ChatRoom.objects.all().delete()


@tag("needs-redis")
class ChatMessageTests(MemberTestCase):
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

  async def test_chat_consumer(self):
    data = {
      'message': "this is my message!",
      'member': self.member.id,
      'username': self.member.username,
      'room': self.slug,
    }
    application = URLRouter(websocket_urlpatterns)
    communicator = WebsocketCommunicator(application, f"/chat/{self.slug}")
    connected, subprotocol = await communicator.connect()
    self.assertTrue(connected)
    # Test sending data as text
    await communicator.send_json_to(data)
    response = await communicator.receive_json_from()
    print(response)
    self.assertEqual(response['message'], data['message'])
    self.assertEqual(response['username'], data['username'])
    msg = await self.get_room_first_msg()
    self.assertIsNotNone(msg)
    self.assertEqual(response['message'], msg.content)
    await self.check_msg_member(msg)
    # Close
    await communicator.disconnect()
