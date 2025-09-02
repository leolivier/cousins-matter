import json
import random
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from urllib.parse import unquote
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.formats import localize  # , date_format
from django.utils import timezone
from django.utils.translation import gettext as _, get_language

from cm_main.followers import check_followers
from cm_main.tests import get_absolute_url
from cm_main.utils import is_testing
from .models import ChatMessage, ChatRoom
from members.models import Member

random.seed()

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
  locale = get_language().replace('-', '_')

  async def connect(self):
    """
    Handles the websocket connection for the given room.

    Upon connection, the consumer adds itself to the room group and
    accepts the connection.

    The room group is named as follows: ``chat_<room_slug>``.

    The accepted connection is then ready to receive messages from
    other members of the room and can send messages to them.

    :param self: The consumer instance.
    :type self: :py:class:`ChatConsumer`
    """
    self.room_slug = self.scope['url_route']['kwargs']['room_slug']
    self.room_group_name = 'chat_%s' % self.room_slug

    # Join room group
    await self.channel_layer.group_add(
      self.room_group_name,
      self.channel_name
    )

    await self.accept()

  async def disconnect(self, close_code):
    """
    Handles the disconnection of a websocket for the given room.

    Upon disconnection, the consumer removes itself from the room group
    and logs the disconnection.

    :param self: The consumer instance.
    :type self: :py:class:`ChatConsumer`
    :param close_code: The close code of the websocket connection.
    :type close_code: int
    """
    await self.channel_layer.group_discard(
      self.room_group_name,
      self.channel_name
    )
    logger.debug(f"websocket disconnected: {close_code}")
    await super().disconnect(close_code)

  async def close(self, code=None, reason=None):
    """
    Closes the websocket connection.

    The connection is closed with the given code and reason.

    :param code: The close code of the websocket connection.
    :type code: int
    :param reason: The reason of the websocket connection closure.
    :type reason: str
    """

    logger.debug(f"websocket closed connection: {code} {reason}")
    await super().close(code, reason)

  @sync_to_async
  def acheck_followers(self, room, message, member, url):
    check_followers(None, room, room.owner(), url, message, member)

# typical self.scope content
# {
# 	'type': 'websocket',
# 	'path': '/chat/a-chat-room-4',
# 	'raw_path': b'/chat/a-chat-room-4',
# 	'root_path': '',
# 	'headers': [
# 		(b'host', b'127.0.0.1:8000'),
# 		(b'user-agent', b'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0'),
# 		(b'accept', b'*/*'),
# 		(b'accept-language', b'fr-FR,en-US;q=0.7,fr;q=0.3'),
# 		(b'accept-encoding', b'gzip, deflate, br, zstd'),
# 		(b'sec-websocket-version', b'13'),
# 		(b'origin', b'http://127.0.0.1:8000'),
# 		(b'sec-websocket-extensions', b'permessage-deflate'),
# 		(b'sec-websocket-key', b'RzYCMMrzBmkgmlrfiaOOqA=='),
# 		(b'dnt', b'1'),
# 		(b'connection', b'keep-alive, Upgrade'),
# 		(b'cookie', b'csrftoken=uo28rDClBtn8WSqPQKE2C7RlkAGKkZIP; sessionid=aiuv54p3xsznwsuu0biwd6bu6ucm74b5'),
# 		(b'sec-fetch-dest', b'empty'),
# 		(b'sec-fetch-mode', b'websocket'),
# 		(b'sec-fetch-site', b'same-origin'),
# 		(b'pragma', b'no-cache'),
# 		(b'cache-control', b'no-cache'),
# 		(b'upgrade', b'websocket')
# 	],
# 	'query_string': b'',
# 	'client': ['127.0.0.1', 43706],
# 	'server': ['127.0.0.1', 8000],
# 	'subprotocols': [],
# 	'asgi': {
# 		'version': '3.0'},
# 		'cookies': {
# 			'csrftoken': 'uo28rDClBtn8WSqPQKE2C7RlkAGKkZIP',
# 			'sessionid': 'aiuv54p3xsznwsuu0biwd6bu6ucm74b5'
# 		},
# 		'session': <django.utils.functional.LazyObject object at 0x7458c85fb6b0>,
# 		'user': <channels.auth.UserLazyObject object at 0x7458c8554da0>,
# 		'path_remaining': '',
# 		'url_route': {
# 			'args': (),
# 			'kwargs': {'room_slug': 'a-chat-room-4'}
# 		}
# 	}
# }
  def _build_absolute_url(self, relative_url):
    # big hack...
    headers = dict(self.scope['headers'])
    origin = headers.get(b'origin', b'').decode()
    if origin == '':
      if is_testing():
        return get_absolute_url(relative_url)
      else:
        raise ValueError("Missing origin header")
    else:
      return f"{origin}{relative_url}"

  async def create_message(self, member_id, room_slug, msg_content):
    # print('room slug: ', room_slug)
    room = await ChatRoom.objects.aget(slug=room_slug)
    member = await Member.objects.aget(pk=member_id)
    message = await ChatMessage.objects.acreate(member=member, room=room, content=msg_content)
    url = self._build_absolute_url(reverse('chat:room', args=[room_slug]))
    await self.acheck_followers(room, message, member, url)
    return message

  async def update_message(self, message_id, msg_content):
    message = await ChatMessage.objects.aget(pk=message_id)
    message.content = msg_content
    message.date_modified = timezone.now()
    await message.asave()
    return message

  async def receive(self, text_data):
    """
    Handles the received message from the WebSocket.
    The message is a request to executed on the server
    """
    # print("websocket received: ", text_data)
    data = json.loads(text_data)
    action = data['action']
    args = data['args']
    match action:
      case 'create_chat_message':
        await self.receive_create_chat_message(args)
      case 'delete_chat_message':
        await self.receive_delete_chat_message(args)
      case 'update_chat_message':
        await self.receive_update_chat_message(args)
      case _:
        raise ValueError(f"Unknown action: {action}")

  async def receive_create_chat_message(self, data):
    """
    Handles the creation of a chat message.
    """
    message = data['message']
    member_id = data['member']
    room_slug = unquote(data['room'])
    # Send message to WebSocket
    mbr = await Member.objects.aget(pk=member_id)
    # Save the new message
    msg = await self.create_message(member_id, room_slug, message)
    # print("saved: ", message, ', now sends to ', self.room_group_name)
    # Then send it to room group so each member can receive it and display it in its own browser
    await self.channel_layer.group_send(
      self.room_group_name,
      {
        'type': 'create_chat_message',
        'message': message,
        'username': mbr.username,
        'full_username': mbr.full_name,
        'member_id': member_id,
        'date_added': localize(timezone.localtime(msg.date_added)),
        'unformated_date_added': msg.date_added.strftime('%Y-%m-%d'),  # for checking if the date has changed
        'member_url': reverse('members:detail', args=[member_id]),
        'msgid': msg.id,
      }
    )
    # print("websocket send: ", message, ' to ', self.room_group_name)

  async def create_chat_message(self, event):
    """
    Sends a creation message to the WebSocket for each connected member of the room.
    """
    await self.send(text_data=json.dumps({
      'action': 'create_chat_message',
      'args': event
    }))
    # print('create_chat_message', args)

  async def check_user_permission(self, msgid):
    "checks if the user in the scope is the owner of the message geiven by msgid"
    message = await ChatMessage.objects.aget(pk=msgid)

    if 'asgi' not in self.scope:
      logger.info('no asgi in data:', self.scope)
      raise ValidationError(f"_('Malformed message: no asgi'):{self.scope}")
    elif 'user' not in self.scope['asgi']:
      logger.info("no user in asgi:", self.scope['asgi'])
      raise ValidationError(_('Malformed message: no user in asgi'))
    else:
      user = self.scope['asgi']['user']
      if user.pk != message.member_id:
        raise PermissionError(_("You can only update or delete your own messages"))

  async def receive_update_chat_message(self, data):
    """
    Handles the update of a chat message.
    """
    message = data['message']
    msgid = data['msgid']
    await self.check_user_permission(msgid)
    # Save the message
    msg = await self.update_message(msgid, message)
    print("updated: ", message, ', now sends to ', self.room_group_name)
    # Send it to room group
    await self.channel_layer.group_send(
      self.room_group_name,
      {
        'type': 'update_chat_message',
        'msgid': msg.id,
        'message': message,
      }
    )
    # print("websocket send: ", message, ' to ', self.room_group_name)

  async def update_chat_message(self, event):
    """
    Sends an update message to the WebSocket for each connected member of the room.
    """
    # Send message to WebSocket
    await self.send(text_data=json.dumps({
      'action': 'update_chat_message',
      'args': event
    }))
    # print('update_chat_message', event)

  async def receive_delete_chat_message(self, data):
    msgid = data['msgid']
    await self.check_user_permission(msgid)
    # delete the message (actually, replacing it by a deletion message)
    del_msg = f'**{_("This message has been deleted")}**'
    await self.update_message(msgid, del_msg)
    # Send "delete" message to room group
    await self.channel_layer.group_send(
      self.room_group_name,
      {
        'type': 'update_chat_message',
        'msgid': msgid,
        'message': del_msg
      }
    )
