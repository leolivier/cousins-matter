import json
from urllib.parse import urlencode
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
# from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from accounts.tests import LoggedAccountTestCase
from .consumers import ChatConsumer
from .models import ChatMessage, ChatRoom


class ChatRoomTests(LoggedAccountTestCase):
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


class ChatMessageTests(LoggedAccountTestCase):
  def setUp(self):
    self.room_name = 'test messages #1'
    self.slug = slugify(self.room_name)
    self.room = ChatRoom.objects.create(name=self.room_name)

  async def test_chat_consumer(self):
    data = {
      'message': "this is my message!",
      'account': 1,
      'username': "anonymous",
      'room': self.slug,
    }
    communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/chat/{self.slug}")
    connected, subprotocol = await communicator.connect()
    self.assertTrue(connected)
    # Test sending data as text
    await communicator.send_to(text_data=json.dumps(data))
    response = await communicator.receive_from()
    print(response)
    self.assertEqual(response, "hello")
    # Close
    await communicator.disconnect()
