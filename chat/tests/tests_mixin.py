from django.template.defaultfilters import slugify
from django.contrib.auth import aget_user
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter

from ..models import ChatRoom
from ..routing import websocket_urlpatterns


@sync_to_async
def astr(obj):
  return str(obj)


class ChatMessageSenderMixin():
  @sync_to_async
  def acreate_member_and_login(self):
    return self.create_member_and_login()

  @sync_to_async
  def apost(self, url, *args, **kwargs):
    return self.client.post(url, *args, **kwargs)

  @sync_to_async
  def alogin_as(self, member):
    return self.login_as(member)

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

  async def send_updated_message(self, room_slug, msgid, msg):
    data = {
      'action': 'update_chat_message',
      'args': {
        'msgid': msgid,
        'message': msg
      }
    }
    return await self._send_msg(room_slug, data, disconnect=True)

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
