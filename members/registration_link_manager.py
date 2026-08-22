from datetime import datetime, timedelta
from django.conf import settings
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36
from base64 import urlsafe_b64encode, urlsafe_b64decode
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


class TokenManager:
  """
  creates and verifies tokens based on the user's email.
  Based on the code from django.contrib.auth.tokens.
  """

  _algorithm = "sha256"
  _secret = settings.SECRET_KEY
  _key_salt = "cousinsmatter.members.check_before_registry.TokenManager"

  def __init__(self) -> None:
    self.max_age = settings.MAX_REGISTRATION_AGE or timedelta(days=2)

  def make_token(self, text):
    """
    Return a token that can be used once.
    """
    return self._make_token_with_timestamp(
      text,
      self._num_seconds(self._now()),
      self._secret,
    )

  def check_token(self, text, token):
    """
    Check that a password reset token is correct for a given text.
    """
    if not (text and token):
      return False
    # Parse the token
    try:
      ts_b36, _ = token.split("-")
    except ValueError:
      return False

    try:
      ts = base36_to_int(ts_b36)
    except ValueError:
      return False

    # Check that the timestamp/uid has not been tampered with
    if not constant_time_compare(
      self._make_token_with_timestamp(text, ts, self._secret),
      token,
    ):
      return False

    # Check the timestamp is within limit.
    if (self._num_seconds(self._now()) - ts) > self.max_age:
      return False

    return True

  def _make_token_with_timestamp(self, text, timestamp, secret):
    # timestamp is number of seconds since 2001-1-1. Converted to base 36,
    # this gives us a 6 digit string until about 2069.
    ts_b36 = int_to_base36(timestamp)
    hash_string = salted_hmac(
      self._key_salt,
      f"{text}:{timestamp}",
      secret=secret,
      algorithm=self._algorithm,
    ).hexdigest()[::2]  # Limit to shorten the URL.
    return "%s-%s" % (ts_b36, hash_string)

  def _num_seconds(self, dt):
    return int((dt - datetime(2001, 1, 1)).total_seconds())

  def _now(self):
    # Used for mocking in tests
    return datetime.now()


class RegistrationLinkManager(TokenManager):
  @staticmethod
  def _payload(email, tenant_id=None):
    """The signed string. Tenant-prefixed (``"<id>:<email>"``) when a tenant is
    bound to the invitation, so it is covered by the HMAC and tamper-evident."""
    return f"{tenant_id}:{email}" if tenant_id else email

  def generate_link(self, request, email, tenant_id=None):
    """Generates an absolute registration/invitation link for ``email``.

    When ``tenant_id`` is given it is bound into the signed token, so the invitee
    is created on that tenant (and the tenant cannot be swapped in the URL).
    """
    payload = self._payload(email, tenant_id)
    token = self.make_token(payload)
    encoded_text = urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")

    link = reverse(
      "members:register",
      args=(
        encoded_text,
        token,
      ),
    )
    return request.build_absolute_uri(link)

  def decrypt_link(self, encoded_email, encoded_token):
    """Verifies the token and returns ``(tenant_id, email)``.

    ``tenant_id`` is ``None`` for links that carry no tenant. On any failure
    (bad base64, missing data, invalid token) returns ``(None, None)``.
    """
    logger.debug(f"\n{'~' * 40}\nDecoding the link {encoded_email}/{encoded_token}\n{'~' * 40}\n")
    try:
      payload = urlsafe_b64decode(encoded_email).decode("UTF-8")
    except Exception:  # malformed base64
      payload = ""
    decoded_token = encoded_token

    if payload and decoded_token and self.check_token(payload, decoded_token):
      # optional tenant prefix "<int>:<email>"
      if ":" in payload:
        head, rest = payload.split(":", 1)
        if head.isdigit():
          return int(head), rest
      return None, payload

    logger.error(f"\n{'~' * 40}\nError occurred in decoding the link!\n{'~' * 40}\n")
    return None, None

  def check_invitation(self, email, tenant_id, token):
    """Validate an ``(email, tenant_id, token)`` triple (e.g. stored in session).

    Used by the social-login adapter, which keeps the three pieces separately.
    """
    return bool(token and self.check_token(self._payload(email, tenant_id), token))
