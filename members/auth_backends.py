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
