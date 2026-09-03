"""Tenant-isolation tests for the chat app (TenantModel conversion).

A member of tenant A must not see, join or post into tenant B's rooms —
through the ORM, the HTTP views or the WebSocket consumer.

The WebSocket tests use the same async style as chat.tests.tests_read_receipts
(URLRouter + async test methods): a plain sync ``await_`` helper deadlocks on
the channels test event loop.
"""

from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from asgiref.sync import sync_to_async

from chat.models import ChatMessage, ChatRoom, PrivateChatRoom
from chat.routing import websocket_urlpatterns
from core.tests.test_django_q import async_django_q_sync_class
from tenants.models import Tenant
from tenants.scoping import set_current_tenant, tenant_context

_PWD = "pw-12345-Aa"


def _make_member(tenant, username):
  from members.models import Member

  with tenant_context(tenant):
    m = Member.objects.create_member(
      username=username,
      password=_PWD,
      email=f"{username}@example.com",
      first_name=username,
      last_name="x",
      is_active=True,
    )
  return m


class ChatTenantORMTests(TestCase):
  """ORM + HTTP view isolation (no event loop needed)."""

  @classmethod
  def setUpTestData(cls):
    cls.tenant_a = Tenant.objects.create(name="CA", slug="chat-a")
    cls.tenant_b = Tenant.objects.create(name="CB", slug="chat-b")
    cls.member_b = _make_member(cls.tenant_b, "chat_member_b")
    with tenant_context(cls.tenant_a):
      cls.room_a = ChatRoom.objects.create(name="General")
    with tenant_context(cls.tenant_b):
      cls.room_b = ChatRoom.objects.create(name="General")  # same slug, other tenant
      cls.msg_b = ChatMessage.objects.create(member=cls.member_b, room=cls.room_b, content="secret B")

  def setUp(self):
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def test_same_slug_two_tenants(self):
    self.assertEqual(self.room_a.slug, self.room_b.slug)
    self.assertNotEqual(self.room_a.tenant_id, self.room_b.tenant_id)

  def test_queryset_isolation(self):
    with tenant_context(self.tenant_a):
      self.assertTrue(ChatRoom.objects.filter(pk=self.room_a.pk).exists())
      self.assertFalse(ChatRoom.objects.filter(pk=self.room_b.pk).exists())
      self.assertFalse(ChatMessage.objects.filter(pk=self.msg_b.pk).exists())

  def test_cross_tenant_room_with_unique_slug_404s(self):
    # a slug that only exists in tenant A: tenant B's member gets a 404
    self.client.force_login(self.member_b)
    resp = self.client.get(reverse("chat:room", args=["only-in-a"]))
    self.assertEqual(resp.status_code, 404)

  def test_private_room_create_is_tenant_scoped(self):
    # the same room name is creatable in both tenants
    with tenant_context(self.tenant_a):
      room = PrivateChatRoom.objects.create(name="Family")
    with tenant_context(self.tenant_b):
      room2 = PrivateChatRoom.objects.create(name="Family")
    self.assertEqual(room.slug, room2.slug)
    self.assertNotEqual(room.tenant_id, room2.tenant_id)


@async_django_q_sync_class
class ChatTenantWSTests(TransactionTestCase):
  """WebSocket: the consumer must never read/write another tenant's data."""

  def setUp(self):
    # TransactionTestCase flushes between tests: no setUpTestData here
    set_current_tenant(None)
    self.tenant_a = Tenant.objects.create(name="WA", slug="chat-ws-a")
    self.tenant_b = Tenant.objects.create(name="WB", slug="chat-ws-b")
    self.member_b = _make_member(self.tenant_b, "ws_member_b")
    with tenant_context(self.tenant_a):
      self.member_a = _make_member(self.tenant_a, "ws_member_a")
      self.room_a = ChatRoom.objects.create(name="Ws Room")
      self.msg_a = ChatMessage.objects.create(member=self.member_a, room=self.room_a, content="A says hi")

  def tearDown(self):
    set_current_tenant(None)

  def _comm(self):
    communicator = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f"chat/ws/{self.room_a.slug}")
    communicator.scope["user"] = self.member_b
    return communicator

  async def test_ws_cannot_post_cross_tenant(self):
    communicator = self._comm()
    connected, _ = await communicator.connect()
    self.assertTrue(connected)
    await communicator.send_to(
      text_data='{"action": "create_chat_message", "args": {"message": "intrusion", '
      '"member": "%s", "room": "%s"}}' % (self.member_b.pk, self.room_a.slug)
    )
    await communicator.disconnect()
    # nothing was written into tenant A's room
    found = await ChatMessage.unscoped.filter(room=self.room_a, content="intrusion").aexists()
    self.assertFalse(found)

  async def test_ws_cannot_update_cross_tenant_message(self):
    communicator = self._comm()
    await communicator.connect()
    await communicator.send_to(
      text_data='{"action": "update_chat_message", "args": {"msgid": "%s", "message": "hacked"}}' % self.msg_a.pk
    )
    await communicator.disconnect()
    message = await ChatMessage.unscoped.aget(pk=self.msg_a.pk)
    content = await sync_to_async(lambda: message.content)()
    self.assertEqual(content, "A says hi")
