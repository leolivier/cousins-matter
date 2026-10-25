from asgiref.sync import sync_to_async
from allauth.account.auth_backends import AuthenticationBackend
from django.contrib.auth.backends import ModelBackend

from .models import Member


class EmailModelBackend(ModelBackend):
  """Email-only login backend.

  The stock ``ModelBackend`` authenticated via ``USERNAME_FIELD = "username"``,
  whose uniqueness is only ``(tenant, username)`` since migration 0017 — not a
  reliable identifier, and tenant-unscoped through ``get_by_natural_key``.
  Login is therefore by email only: the ``username`` kwarg is kept (hardcoded
  by ``AuthenticationForm.authenticate``) but carries the email.

  The lookup is global (cross-tenant), like ``get_by_natural_key``: email
  uniqueness is enforced globally by the ``member_email_uniq`` constraint.
  """

  def authenticate(self, request, username=None, password=None, **kwargs):
    if username is None or password is None:
      return None
    # Iterate over candidates: transition safety if duplicate emails predate
    # the uniqueness migration — first matching password wins, never a 500.
    for user in Member.unscoped.filter(email__iexact=username):
      if user.check_password(password) and self.user_can_authenticate(user):
        return user
    # No candidate: burn one hash anyway so the timing matches the
    # candidate-found path (same user-enumeration mitigation as upstream).
    Member().set_password(password)
    return None

  async def aauthenticate(self, request, username=None, password=None, **kwargs):
    """Async twin of ``authenticate``.

    ``ModelBackend`` ships a native-async ``aauthenticate`` that does NOT call
    ``self.authenticate``: it looks the user up by ``USERNAME_FIELD``
    (``aget_by_natural_key``), which would silently re-enable username login
    on the async path (ASGI/Channels requests, async test clients).
    """
    if username is None or password is None:
      return None
    async for user in Member.unscoped.filter(email__iexact=username):
      if await user.acheck_password(password) and self.user_can_authenticate(user):
        return user
    # Timing-attack burn, same as the sync path (password hashing is pure CPU,
    # no DB access, so it is safe to call from async code).
    Member().set_password(password)
    return None


class AllauthEmailBackend(AuthenticationBackend):
  """allauth backend forced through its sync ``authenticate``.

  allauth inherits ``ModelBackend``'s native-async ``aauthenticate``, which
  looks the user up by ``USERNAME_FIELD`` through ``aget_by_natural_key``,
  bypassing allauth's own ``LOGIN_METHODS`` logic on the async path
  (ASGI/Channels requests). Wrapping the sync ``authenticate`` keeps allauth
  behaviour (email-only) identical in sync and async contexts.
  """

  async def aauthenticate(self, request, **credentials):
    return await sync_to_async(self.authenticate)(request, **credentials)
