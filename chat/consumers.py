import json
import random
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from tenants.models import Tenant
from tenants.scoping import set_current_tenant
from urllib.parse import unquote
from django.urls import reverse
from django.utils.formats import date_format
from django.utils import timezone
from django.utils.translation import gettext as _, get_language
from django.template.loader import render_to_string
from core.utils import get_test_absolute_url
from core.followers import check_followers
from .models import ChatMessage, ChatRoom
from members.models import Member

random.seed()

logger = logging.getLogger(__name__)


# typical self.scope content in an AsyncWebsocketConsumer
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


class ChatConsumer(AsyncWebsocketConsumer):
  locale = get_language().replace("-", "_")

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
    logger.debug("websocket connected")
    self.room_slug = self.scope["url_route"]["kwargs"]["room_slug"]
    self.room_group_name = "chat_%s" % self.room_slug

    # Join room group
    await self.channel_layer.group_add(self.room_group_name, self.channel_name)

    await self.accept()

    # In private rooms, mark all previously received messages as read by the
    # connecting user and broadcast the updated receipts to the room group.
    user = self.scope.get("user")
    if user is not None and not user.is_anonymous:
      # Defensive: activate the member's tenant for this connection. Inert today
      # (chat is not yet a TenantModel). Use tenant_id (NOT user.tenant: the FK
      # descriptor runs a query, illegal in async context) and a shallow Tenant
      # instance — the scoping layer only reads .pk. When chat is scoped, the
      # global group name must become tenant-prefixed ("chat_<tenant>_<slug>")
      # and each DB touch wrapped in tenant_context() (plan Phase J).
      if not getattr(user, "is_superuser", False):
        tenant_id = getattr(user, "tenant_id", None)
        if tenant_id is not None:
          set_current_tenant(Tenant(pk=tenant_id))
      try:
        room = await ChatRoom.objects.aget(slug=self.room_slug)
      except ChatRoom.DoesNotExist:
        room = None
      if room is not None and not await room.ais_public():
        newly_marked = await self._mark_room_read(user, room)
        if newly_marked:
          await self._broadcast_read_status(room, newly_marked)

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
    set_current_tenant(None)
    await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
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

  def _build_absolute_url(self, relative_url):
    # big hack...
    headers = dict(self.scope["headers"])
    origin = headers.get(b"origin", b"").decode()
    if origin == "":
      from django.conf import settings

      if settings.TESTING:
        return get_test_absolute_url(relative_url)
      else:
        raise ValueError("Missing origin header")
    else:
      return f"{origin}{relative_url}"

  async def acreate_message(self, member_id, room_slug, msg_content):
    # print('room slug: ', room_slug)
    room = await ChatRoom.objects.aget(slug=room_slug)
    member = await Member.objects.aget(pk=member_id)
    message = await ChatMessage.objects.acreate(member=member, room=room, content=msg_content)
    url = self._build_absolute_url(reverse("chat:room", args=[room_slug]))
    await sync_to_async(check_followers)(None, room, await room.aowner(), url, new_internal_object=message, author=member)
    return message

  async def aupdate_message(self, message_id, msg_content):
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
    action = data["action"]
    args = data["args"]
    match action:
      case "create_chat_message":
        await self.receive_create_chat_message(args)
      case "delete_chat_message":
        await self.receive_delete_chat_message(args)
      case "update_chat_message":
        await self.receive_update_chat_message(args)
      case _:
        raise ValueError(f"Unknown action: {action}")

  async def receive_create_chat_message(self, data):
    """
    Handles the creation of a chat message.
    """
    message = data["message"]
    member_id = str(data["member"])
    room_slug = unquote(data["room"])
    # retrieve previous message author
    prev_msg = await ChatMessage.objects.filter(room__slug=room_slug).order_by("-date_added").afirst()
    prev_msg_author_id = str(prev_msg.member_id) if prev_msg else None
    prev_msg_date_added = prev_msg.date_added if prev_msg else None
    mbr = await Member.objects.aget(pk=member_id)
    # Save the new message
    msg = await self.acreate_message(member_id, room_slug, message)
    local_date_added = timezone.localtime(msg.date_added)
    # Then send it to room group so each member can receive it and display it in its own browser
    context = {
      "type": "create_chat_message",
      "content": msg.content,
      "member_id": member_id,
      "member_name": mbr.username,
      "member_fullname": mbr.get_full_name(),
      "member_changed": prev_msg_author_id != member_id if prev_msg_author_id else True,
      "date_changed": prev_msg_date_added.date() != msg.date_added.date() if prev_msg_date_added else True,
      "msg_id": msg.id,
      "date_added": date_format(local_date_added, "DATE_FORMAT"),
      "time_added": date_format(local_date_added, "TIME_FORMAT"),
    }
    # Read-receipt context: a freshly created message is unread by recipients,
    # and receipts only show in private rooms (the fragment template gates on `private`).
    room = await ChatRoom.objects.aget(slug=room_slug)
    context["private"] = not await room.ais_public()
    context["read_status"] = "unread"
    await self.channel_layer.group_send(self.room_group_name, context)

  async def create_chat_message(self, event):
    """
    Sends a creation message to the WebSocket for each connected member of the room.
    """
    user = self.scope.get("user")
    user_id = user.id if user and not user.is_anonymous else None
    context = {"user_id": str(user_id), **event}
    rendered_message = render_to_string("chat/room_detail.html#message_div", context)
    await self.send(text_data=json.dumps({"action": "create_chat_message", "args": {"rendered_message": rendered_message}}))
    # print('create_chat_message', args)

    # In a private room, the recipient (any connected member other than the
    # sender) reads the message as soon as it is delivered: mark it read and
    # broadcast the updated receipt so the sender's check flips ✓ → ✓✓.
    if not event.get("private") or user_id is None or str(user_id) == str(event.get("member_id")):
      return
    room = await ChatRoom.objects.aget(slug=self.room_slug)
    newly = await self._mark_room_read(user, room, only_msg_id=event.get("msg_id"))
    if newly:
      await self._broadcast_read_status(room, newly)

  async def check_user_permission(self, msgid):
    """Checks whether the logged-in user is the owner of the message

    Args:
        msgid: ID of the message to check

    Returns:
        bool: True if the user is the owner, False otherwise

    """
    try:
      message = await ChatMessage.objects.aget(pk=msgid)
      user = self.scope.get("user")

      if not user or user.is_anonymous:
        msg = _("User not authenticated")
        logger.warning(f"Permission denied for message {msgid}: {msg}")
        await self.send(text_data=json.dumps({"action": "error", "error": msg}))
        return False

      if message.member_id != user.id:
        msg = _("You can only update or delete your own messages")
        logger.warning(f"Permission denied for message {msgid}: {msg}")
        await self.send(text_data=json.dumps({"action": "error", "error": msg}))
        return False

    except ChatMessage.DoesNotExist:
      msg = _("Message does not exist")
      logger.warning(f"Permission denied for message {msgid}: {msg}")
      await self.send(text_data=json.dumps({"action": "error", "error": msg}))
      return False
    except Exception as e:
      logger.error(f"Error checking permissions for message {msgid}: {str(e)}")
      await self.send(
        text_data=json.dumps({
          "action": "error",
          "error": _("An error occurred while checking permissions."),
        })
      )
      return

    return True

  async def receive_update_chat_message(self, data):
    """
    Handles the update of a chat message.

    Args:
        data: dict containing 'message' (new message content) and 'msgid' (message ID)
    """
    try:
      message = data["message"]
      msgid = data["msgid"]

      if not await self.check_user_permission(msgid):
        return
      msg = await self.aupdate_message(msgid, message)
      logger.info(f"Message {msgid} updated successfully")

      # Send the update to all members of the group
      await self.channel_layer.group_send(
        self.room_group_name,
        {
          "type": "update_chat_message",
          "msgid": msg.id,
          "message": message,
        },
      )

    except Exception as e:
      logger.error(f"Error updating message {msgid}: {str(e)}")
      await self.send(
        text_data=json.dumps({
          "action": "error",
          "error": f"{_('An error occurred while updating the message')}: {str(e)}",
        })
      )

  async def update_chat_message(self, event):
    """
    Sends an update message to the WebSocket for each connected member of the room.
    """
    # Send message to WebSocket
    await self.send(text_data=json.dumps({"action": "update_chat_message", "args": event}))
    # print('update_chat_message', event)

  async def receive_delete_chat_message(self, data):
    """
    Handles the deletion of a chat message by replacing it with a deletion notice.

    Args:
        data: dict containing 'msgid' (message ID to delete)
    """
    try:
      msgid = data["msgid"]

      # Check user permissions
      if not await self.check_user_permission(msgid):
        return
      del_msg = f"**{_('This message has been deleted')}**"
      await self.aupdate_message(msgid, del_msg)
      logger.info(f"Message {msgid} marked as deleted")

      # Send the deletion notice to all members of the group
      await self.channel_layer.group_send(
        self.room_group_name,
        {"type": "update_chat_message", "msgid": msgid, "message": del_msg},
      )

    except Exception as e:
      logger.error(f"Error marking message {msgid} as deleted: {str(e)}")
      await self.send(
        text_data=json.dumps({
          "action": "error",
          "error": f'_("An error occurred while deleting the message"): {str(e)}',
        })
      )

  async def _mark_room_read(self, member, room, only_msg_id=None):
    """Marks messages in ``room`` as read by ``member``.

    Targets messages received by ``member`` (sender != member) not yet marked read.
    ``only_msg_id`` restricts the marking to one message (real-time delivery);
    when ``None`` all eligible messages are marked (room just opened).

    Returns the list of message ids newly marked, so callers can recompute and
    broadcast their aggregate read status. No-op for public rooms.
    """
    if await room.ais_public():
      return []
    qs = ChatMessage.objects.filter(room=room).exclude(member=member).exclude(read_by=member)
    if only_msg_id is not None:
      qs = qs.filter(pk=only_msg_id)
    msg_ids = await sync_to_async(list)(qs.values_list("id", flat=True))
    if not msg_ids:
      return []
    # Bulk-insert the read receipts via the auto M2M `through` table; ignore
    # conflicts so concurrent reads (a race between two members) don't raise.
    read_through = ChatMessage.read_by.through
    await read_through.objects.abulk_create(
      [read_through(chatmessage_id=mid, member_id=member.id) for mid in msg_ids],
      ignore_conflicts=True,
    )
    return msg_ids

  async def _broadcast_read_status(self, room, msg_ids):
    """Recomputes the aggregate read status of ``msg_ids`` and broadcasts a single
    grouped ``read_status_update`` event to the room group.

    The status is recomputed from the DB (not derived locally) so reads by other
    members between the marking and the broadcast are reflected.
    """
    member_ids = set(await sync_to_async(list)(room.followers.values_list("id", flat=True)))
    member_count = len(member_ids)
    updates = []
    async for msg in ChatMessage.objects.filter(pk__in=msg_ids):
      read_count = await msg.read_by.filter(id__in=member_ids).acount()
      status = ChatMessage.compute_status(
        is_public=False,
        room_members_count=member_count,
        read_count=read_count,
        sender_is_member=msg.member_id in member_ids,
      )
      updates.append({"msg_id": msg.id, "status": status.value})
    if not updates:
      return
    await self.channel_layer.group_send(
      self.room_group_name,
      {"type": "read_status_update", "updates": updates},
    )

  async def read_status_update(self, event):
    """Channel handler: forwards the read-receipt updates to the client."""
    await self.send(text_data=json.dumps({"action": "read_status_update", "args": {"updates": event["updates"]}}))
