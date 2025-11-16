from django.template.defaultfilters import slugify
from django.contrib.auth import aget_user
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.contrib.auth import get_user_model
from ..models import ChatRoom
from ..routing import websocket_urlpatterns


@sync_to_async
def astr(obj):
  return str(obj)


class ChatMessageSenderMixin(object):
  async def _send_msg(self, room_slug, data, disconnect):
    "Actually sends a message to a chat room."
    application = URLRouter(websocket_urlpatterns)
    # Get the currently logged-in user
    # user = await sync_to_async(lambda: self.client.session.get('_auth_user_id'))()
    # user_obj = await sync_to_async(get_user_model().objects.get)(pk=user)
    user = await self.client.session.aget('_auth_user_id')
    user_obj = await get_user_model().objects.aget(pk=user)

    communicator = WebsocketCommunicator(
        application=application,
        path=f"/chat/{room_slug}",
    )
    communicator.scope['user'] = user_obj
    connected, _ = await communicator.connect()
    self.assertTrue(connected)
    # Test sending data as text
    await communicator.send_json_to(data)
    if disconnect:
      await communicator.disconnect()
    else:
      return communicator

  async def send_chat_message(self, msg, room_slug, disconnect=True):
    "Sends a chat message to a room."
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

  async def send_updated_message(self, room_slug, msgid, msg, disconnect=True):
    "Sends an updated chat message to a room."
    data = {
      'action': 'update_chat_message',
      'args': {
        'msgid': msgid,
        'message': msg
      }
    }
    return await self._send_msg(room_slug, data, disconnect)

  async def send_delete_message(self, room_slug, msgid, disconnect=True):
    "Sends a delete chat message to a room."
    data = {
      'action': 'delete_chat_message',
      'args': {
        'msgid': msgid
      }
    }
    return await self._send_msg(room_slug, data, disconnect)

  def setUp(self):
    "All tests start with a new room."
    super().setUp()
    self.room_name = 'test messages #1'
    self.slug = slugify(self.room_name)
    self.room = ChatRoom.objects.create(name=self.room_name)

  def tearDown(self):
    "All tests end with the room being deleted."
    self.room.delete()
    self.room = None
    super().tearDown()
