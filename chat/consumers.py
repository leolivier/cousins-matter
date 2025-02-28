import json
import random
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from urllib.parse import unquote
# from django.conf import settings
from django.urls import reverse
from django.utils.formats import localize  # , date_format
from django.utils import timezone
from django.utils.translation import gettext as _, get_language

from cm_main.followers import check_followers
from cm_main.tests import get_absolute_url
from cousinsmatter.utils import is_testing
from .models import ChatMessage, ChatRoom
from members.models import Member

random.seed()

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
  locale = get_language().replace('-', '_')

  async def connect(self):
    self.room_slug = self.scope['url_route']['kwargs']['room_slug']
    self.room_group_name = 'chat_%s' % self.room_slug

    # Join room group
    await self.channel_layer.group_add(
      self.room_group_name,
      self.channel_name
    )

    await self.accept()

  async def disconnect(self, close_code):
    # Leave room group
    await self.channel_layer.group_discard(
      self.room_group_name,
      self.channel_name
    )
    logger.debug(f"websocket disconnected: {close_code}")
    await super().disconnect(close_code)

  async def close(self, code=None, reason=None):
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

  async def save_message(self, member_id, room_slug, msg_content):
    # print('room slug: ', room_slug)
    room = await ChatRoom.objects.aget(slug=room_slug)
    member = await Member.objects.aget(pk=member_id)
    message = await ChatMessage.objects.acreate(member=member, room=room, content=msg_content)
    url = self._build_absolute_url(reverse('chat:room', args=[room_slug]))
    await self.acheck_followers(room, message, member, url)
    return message

  # Receive message from WebSocket
  async def receive(self, text_data):
    data = json.loads(text_data)
    action = data['action']
    args = data['args']
    match action:
      case 'create_chat_message':
        await self.receive_create_chat_message(args)
      case 'delete_chat_message':
        await self.receive_delete_chat_message(args)
      case _:
        raise ValueError(f"Unknown action: {action}")

  async def receive_create_chat_message(self, data):
    message = data['message']
    member_id = data['member']
    username = data['username']
    room_slug = unquote(data['room'])
    # Save the message
    msg = await self.save_message(member_id, room_slug, message)
    # Send it to room group
    await self.channel_layer.group_send(
      self.room_group_name,
      {
        'type': 'create_chat_message',
        'message': message,
        'username': username,
        'date_added': localize(timezone.localtime(msg.date_added)),
        # format_datetime(msg.date_added, tzinfo=settings.TIME_ZONE, locale=self.locale),
        'msgid': msg.id,
      }
    )

  # Receive message from room group
  async def create_chat_message(self, event):
    # create delete_url and member_url
    msgid = event['msgid']
    msg = await ChatMessage.objects.aget(pk=msgid)
    # Send message to WebSocket
    await self.send(text_data=json.dumps({
      'action': 'create_chat_message',
      'args': {
        'message': event['message'],
        'username': event['username'],
        'date_added': event['date_added'],
        'msgid': msgid,
        'member_url': reverse('members:detail', args=[msg.member_id]),
      }
    }))

  async def receive_delete_chat_message(self, data):
    msgid = data['msgid']
    message = await ChatMessage.objects.aget(pk=msgid)
    if 'asgi' not in self.scope:
      logger.info('no asgi in data:', self.scope)
    elif 'user' not in self.scope['asgi']:
      logger.info("no user in asgi:", self.scope['asgi'])
    else:
      user = self.scope['asgi']['user']
      if user.pk != message.member_id:
        raise PermissionError(_("You can only delete your own messages"))
    # delete the message
    await message.adelete()
    # print("message deleted!", msgid)
    # Send delete message to room group
    await self.channel_layer.group_send(
      self.room_group_name,
      {
        'type': 'delete_chat_message',
        'msgid': msgid
      }
    )

  async def delete_chat_message(self, event):
    # Send message to WebSocket
    await self.send(text_data=json.dumps({
      'action': 'delete_chat_message',
      'args': {
        'msgid': event['msgid'],
      }
    }))
