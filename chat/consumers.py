import json
import random
from babel.dates import format_datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from urllib.parse import unquote
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import ChatMessage, ChatRoom

random.seed()


class ChatConsumer(AsyncWebsocketConsumer):
  locale = settings.LANGUAGE_CODE.replace('-', '_')

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

  @sync_to_async
  def save_message(self, account_id, room_slug, message):
    print('room slug: ', room_slug)
    room = ChatRoom.objects.get(slug=room_slug)
    User = get_user_model()
    account = User.objects.get(pk=account_id)
    chat = ChatMessage.objects.create(account=account, room=room, content=message)
    return chat

  # Receive message from WebSocket
  async def receive(self, text_data):
    data = json.loads(text_data)
    message = data['message']
    account_id = data['account']
    username = data['username']
    room_slug = unquote(data['room'])
    # Save the message
    msg = await self.save_message(account_id, room_slug, message)
    # Send it to room group
    await self.channel_layer.group_send(
      self.room_group_name,
      {
        'type': 'chat_message',
        'message': message,
        'username': username,
        'date_added': format_datetime(msg.date_added, tzinfo=settings.TIME_ZONE, locale=self.locale),
      }
    )

  # Receive message from room group
  async def chat_message(self, event):
    message = event['message']
    username = event['username']
    date_added = event['date_added']

    # Send message to WebSocket
    await self.send(text_data=json.dumps({
      'message': message,
      'username': username,
      'date_added': date_added
    }))
