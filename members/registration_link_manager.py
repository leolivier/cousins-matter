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
    ).hexdigest()[
      ::2
    ]  # Limit to shorten the URL.
    return "%s-%s" % (ts_b36, hash_string)

  def _num_seconds(self, dt):
    return int((dt - datetime(2001, 1, 1)).total_seconds())

  def _now(self):
    # Used for mocking in tests
    return datetime.now()


class RegistrationLinkManager(TokenManager):
  def generate_link(self, request, text):
    """
    Generates link for the text.
    """
    token = self.make_token(text)
    encoded_text = urlsafe_b64encode(str(text).encode('utf-8')).decode('utf-8')

    link = reverse("members:register", args=(encoded_text, token, ))
    absolute_link = request.build_absolute_uri(link)
    return absolute_link

  def decrypt_link(self, encoded_email, encoded_token):
    """
    main verification and decryption happens here.
    """
    logger.info(f'\n{"~" * 40}\nDecoding the link {encoded_email}/{encoded_token}\n{"~" * 40}\n')
    decoded_email = urlsafe_b64decode(encoded_email).decode('UTF-8')
    # decoded_token = urlsafe_b64decode(encoded_token).decode('UTF-8')
    decoded_token = encoded_token

    if decoded_email and decoded_token:
      if self.check_token(decoded_email, decoded_token):
        return decoded_email
    else:
      logger.error(f'\n{"~" * 40}\nError occurred in decoding the link!\n{"~" * 40}\n')
      return False
