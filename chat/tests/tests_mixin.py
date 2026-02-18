from django.template.defaultfilters import slugify
from django.contrib.auth import aget_user
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.contrib.auth import get_user_model
from ..models import ChatRoom
from ..routing import websocket_urlpatterns


class ChatMessageSenderMixin(object):
  async def _send_msg(self, room_slug, data, disconnect, sender=None):
    "Actually sends a message to a chat room."
    application = URLRouter(websocket_urlpatterns)
    # Get the currently logged-in user
    if sender is None:
      session = await sync_to_async(getattr)(self.async_client, "session")
      user_id = await session.aget("_auth_user_id")
      user = await get_user_model().objects.aget(pk=user_id)
    else:
      user = sender

    communicator = WebsocketCommunicator(application, f"chat/{room_slug}")
    communicator.scope["user"] = user
    connected, _ = await communicator.connect()
    if not connected:
      raise Exception(f"Failed to connect to WebSocket for room {room_slug}")
    await communicator.send_json_to(data)
    if disconnect:
      await communicator.disconnect()
    return communicator

  async def send_chat_message(self, msg, room_slug, disconnect=True, sender=None):
    "Sends a chat message to a room."
    # sender is the currently connected user
    if sender is None:
      await sync_to_async(getattr)(self.async_client, "session")
      sender = await aget_user(self.async_client)
    data = {
      "action": "create_chat_message",
      "args": {
        "message": msg,
        "member": sender.id,
        "username": sender.username,
        "room": room_slug,
      },
    }
    return await self._send_msg(room_slug, data, disconnect, sender=sender)

  async def send_updated_message(self, room_slug, msgid, msg, disconnect=True, sender=None):
    "Sends an updated chat message to a room."
    # sender is the currently connected user
    if sender is None:
      await sync_to_async(getattr)(self.async_client, "session")
      sender = await aget_user(self.async_client)
    data = {
      "action": "update_chat_message",
      "args": {"msgid": msgid, "message": msg},
    }
    return await self._send_msg(room_slug, data, disconnect, sender=sender)

  async def send_delete_message(self, room_slug, msgid, disconnect=True, sender=None):
    "Sends a delete chat message to a room."
    # sender is the currently connected user
    if sender is None:
      await sync_to_async(getattr)(self.async_client, "session")
      sender = await aget_user(self.async_client)
    data = {"action": "delete_chat_message", "args": {"msgid": msgid}}
    return await self._send_msg(room_slug, data, disconnect, sender=sender)

  def setUp(self):
    "All tests start with a new room."
    super().setUp()
    self.room_name = "test messages #1"
    self.slug = slugify(self.room_name)
    self.room = ChatRoom.objects.create(name=self.room_name)

  def tearDown(self):
    "All tests end with the room being deleted."
    self.room.delete()
    self.room = None
    super().tearDown()
