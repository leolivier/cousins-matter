"""Regression tests for the email-only authentication backend.

``ModelBackend`` ships a native-async ``aauthenticate`` that looks the user up
by ``USERNAME_FIELD`` (username), bypassing ``authenticate()``. Without an
``aauthenticate`` override in ``EmailModelBackend`` (and without wrapping
allauth's backend), username login silently came back on the async path
(ASGI/Channels, async test clients) although the sync path was email-only.
"""

from members.tests.tests_member_base import AsyncMemberTestCase


class AsyncEmailBackendTest(AsyncMemberTestCase):
  async def test_alogin_by_email(self):
    member = await self.acreate_member(is_active=True)
    self.assertTrue(await self.async_client.alogin(username=member.email, password=member.password))

  async def test_alogin_by_username_rejected(self):
    member = await self.acreate_member(is_active=True)
    self.assertFalse(await self.async_client.alogin(username=member.username, password=member.password))
