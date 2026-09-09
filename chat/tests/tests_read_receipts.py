"""Tests for private-room read receipts (issue #130).

Covers:
- ``ChatMessage.read_status()`` aggregate derivation (unit, sync).
- The ``ChatConsumer`` marking messages read on connect and on real-time
  delivery, broadcasting ``read_status_update``, and leaving public rooms alone.
"""

from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.db import connection
from django.test import tag
from django.test.utils import CaptureQueriesContext

from chat.models import ChatMessage, ChatRoom, MessageStatus, PrivateChatRoom
from chat.routing import websocket_urlpatterns
from chat.services import compute_read_updates
from chat.tests.tests_mixin import ChatMessageSenderMixin
from core.tests.test_django_q import async_django_q_sync_class
from members.tests.tests_member_base import AsyncMemberTestCase, MemberTestCase


class ReadReceiptModelTests(MemberTestCase):
  """Unit tests for ChatMessage.read_status() (no WebSocket)."""

  def _private_room(self, *members):
    room = PrivateChatRoom.objects.create(name="private receipt room")
    for m in members:
      room.followers.add(m)
    return room

  def test_public_room_status_is_none(self):
    room = ChatRoom.objects.create(name="a public room")
    msg = ChatMessage.objects.create(member=self.member, room=room, content="hi")
    self.assertIsNone(msg.read_status())

  def test_single_member_private_room_is_unread(self):
    room = self._private_room(self.member)
    msg = ChatMessage.objects.create(member=self.member, room=room, content="hi")
    # no recipients -> nothing to acknowledge
    self.assertEqual(msg.read_status(), MessageStatus.UNREAD)

  def test_two_members_unread_then_read(self):
    other = self.create_member(is_active=True)
    room = self._private_room(self.member, other)
    msg = ChatMessage.objects.create(member=self.member, room=room, content="hi")
    self.assertEqual(msg.read_status(), MessageStatus.UNREAD)
    msg.read_by.add(other)
    self.assertEqual(msg.read_status(), MessageStatus.READ)

  def test_three_members_partially_then_read(self):
    m2 = self.create_member(is_active=True)
    m3 = self.create_member(is_active=True)
    room = self._private_room(self.member, m2, m3)
    msg = ChatMessage.objects.create(member=self.member, room=room, content="hi")
    self.assertEqual(msg.read_status(), MessageStatus.UNREAD)
    msg.read_by.add(m2)
    self.assertEqual(msg.read_status(), MessageStatus.PARTIALLY_READ)
    msg.read_by.add(m3)
    self.assertEqual(msg.read_status(), MessageStatus.READ)


@tag("needs-redis")
@async_django_q_sync_class
class ReadReceiptConsumerTests(ChatMessageSenderMixin, AsyncMemberTestCase):
  """Async WebSocket tests for read-receipt marking and broadcast."""

  async def _connect(self, member, room):
    communicator = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f"chat/ws/{room.slug}")
    communicator.scope["user"] = member
    connected, _ = await communicator.connect()
    self.assertTrue(connected, f"Failed to connect to WebSocket for room {room.slug}")
    return communicator

  async def test_connect_marks_past_messages_read_and_broadcasts(self):
    """B opening the room marks A's prior message read; A receives read_status_update."""
    member2 = await self.acreate_member(is_active=True)
    room = await sync_to_async(PrivateChatRoom.objects.create)(name="connect receipt room")
    await sync_to_async(room.followers.add)(self.member, member2)

    # A sends a message while connected (keep its socket open to capture the broadcast).
    comm_a = await self.send_chat_message("hello there", room.slug, disconnect=False, sender=self.member)
    await comm_a.receive_json_from()  # consume A's own create_chat_message echo

    # B connects -> marks the message read -> broadcasts read_status_update
    comm_b = await self._connect(member2, room)
    update = await comm_a.receive_json_from()
    self.assertEqual(update["action"], "read_status_update")
    self.assertEqual(update["args"]["updates"][0]["status"], MessageStatus.READ.value)

    msg = await ChatMessage.objects.aget(room=room)
    self.assertTrue(await msg.read_by.filter(pk=member2.pk).aexists())
    # the sender is never marked as a reader of their own message
    self.assertFalse(await msg.read_by.filter(pk=self.member.pk).aexists())

    await comm_a.disconnect()
    await comm_b.disconnect()

  async def test_realtime_message_marked_read(self):
    """With both connected, A's new message is read by B as it is delivered."""
    member2 = await self.acreate_member(is_active=True)
    room = await sync_to_async(PrivateChatRoom.objects.create)(name="realtime receipt room")
    await sync_to_async(room.followers.add)(self.member, member2)

    comm_a = await self._connect(self.member, room)
    comm_b = await self._connect(member2, room)

    await comm_a.send_json_to({
      "action": "create_chat_message",
      "args": {"message": "hi live", "member": self.member.id, "username": self.member.username, "room": room.slug},
    })

    # A receives its own create echo, then the read receipt once B's delivery marks it read.
    update = None
    for _ in range(4):
      received = await comm_a.receive_json_from()
      if received.get("action") == "read_status_update":
        update = received
        break
    self.assertIsNotNone(update, "A never received a read_status_update")
    self.assertEqual(update["args"]["updates"][0]["status"], MessageStatus.READ.value)

    msg = await ChatMessage.objects.aget(room=room)
    self.assertTrue(await msg.read_by.filter(pk=member2.pk).aexists())

    await comm_a.disconnect()
    await comm_b.disconnect()

  async def test_public_room_has_no_receipt(self):
    """Public rooms render no read receipt and broadcast no read_status_update."""
    comm_a = await self.send_chat_message("public hi", self.room.slug, disconnect=False, sender=self.member)
    response = await comm_a.receive_json_from()
    rendered = response["args"]["rendered_message"]
    self.assertNotIn("read-receipt", rendered)
    await comm_a.disconnect()


class ComputeReadUpdatesTests(MemberTestCase):
  """``compute_read_updates`` must stay O(1) in queries, not O(messages)."""

  def _room_with_messages(self, name, n):
    other = self.create_member(is_active=True)
    room = PrivateChatRoom.objects.create(name=name)
    room.followers.add(self.member, other)
    msgs = [ChatMessage.objects.create(member=self.member, room=room, content=f"m{i}") for i in range(n)]
    return room, msgs

  def test_statuses_are_computed(self):
    other = self.create_member(is_active=True)
    room = PrivateChatRoom.objects.create(name="compute updates statuses room")
    room.followers.add(self.member, other)
    msg = ChatMessage.objects.create(member=self.member, room=room, content="hi")
    updates = compute_read_updates(room, [msg.id])
    self.assertEqual(updates[0]["msg_id"], msg.id)
    self.assertEqual(updates[0]["status"], MessageStatus.UNREAD.value)
    msg.read_by.add(other)
    updates = compute_read_updates(room, [msg.id])
    self.assertEqual(updates[0]["status"], MessageStatus.READ.value)

  def test_query_count_does_not_scale_with_messages(self):
    room, msgs = self._room_with_messages("compute updates 5 room", 5)
    with CaptureQueriesContext(connection) as ctx5:
      updates = compute_read_updates(room, [m.id for m in msgs])
    self.assertEqual(len(updates), 5)
    room2, msgs2 = self._room_with_messages("compute updates 10 room", 10)
    with CaptureQueriesContext(connection) as ctx10:
      updates2 = compute_read_updates(room2, [m.id for m in msgs2])
    self.assertEqual(len(updates2), 10)
    self.assertEqual(len(ctx10), len(ctx5))
