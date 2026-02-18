from datetime import datetime
from django.test import TestCase, RequestFactory
from base64 import urlsafe_b64encode
from unittest.mock import patch
from ..registration_link_manager import TokenManager, RegistrationLinkManager


class TokenManagerTests(TestCase):
  def setUp(self):
    self.manager = TokenManager()
    self.text = "test@example.com"

  def test_make_and_check_token_success(self):
    token = self.manager.make_token(self.text)
    self.assertTrue(self.manager.check_token(self.text, token))

  def test_check_token_missing_args(self):
    self.assertFalse(self.manager.check_token("", "token"))
    self.assertFalse(self.manager.check_token("text", ""))

  def test_check_token_malformed(self):
    self.assertFalse(self.manager.check_token(self.text, "invalidtoken"))

  def test_check_token_invalid_timestamp_base36(self):
    # Token format is ts_b36-hash
    self.assertFalse(self.manager.check_token(self.text, "invalid-hash"))

  def test_check_token_tampered_hash(self):
    token = self.manager.make_token(self.text)
    ts, hash_val = token.split("-")
    tampered_token = f"{ts}-{hash_val[:-1]}0"
    self.assertFalse(self.manager.check_token(self.text, tampered_token))

  def test_check_token_expired(self):
    # Mock _now to return a date far in the past when making token
    # Or mock _now to return a date far in the future when checking
    with patch.object(TokenManager, "_now") as mock_now:
      past_date = datetime(2020, 1, 1)
      mock_now.return_value = past_date
      token = self.manager.make_token(self.text)

      # Now mock _now to present time
      mock_now.return_value = datetime.now()
      self.assertFalse(self.manager.check_token(self.text, token))


class RegistrationLinkManagerTests(TestCase):
  def setUp(self):
    self.manager = RegistrationLinkManager()
    self.factory = RequestFactory()
    self.email = "test@example.com"

  def test_generate_link(self):
    request = self.factory.get("/")
    link = self.manager.generate_link(request, self.email)
    self.assertIn("http://testserver", link)
    self.assertIn("/members/register/", link)

  def test_decrypt_link_success(self):
    request = self.factory.get("/")
    link = self.manager.generate_link(request, self.email)
    # Link format: .../register/<encoded_email>/<token>/
    parts = link.split("/")
    # parts might be ['', 'members', 'register', '<encoded>', '<token>', '']
    # Let's find register and get next two
    reg_idx = parts.index("register")
    encoded_email = parts[reg_idx + 1]
    token = parts[reg_idx + 2]

    decrypted_email = self.manager.decrypt_link(encoded_email, token)
    self.assertEqual(decrypted_email, self.email)

  def test_decrypt_link_invalid_token(self):
    encoded_email = urlsafe_b64encode(self.email.encode("utf-8")).decode("utf-8")
    self.assertFalse(self.manager.decrypt_link(encoded_email, "invalid-token"))

  def test_decrypt_link_missing_data(self):
    # decrypt_link(self, encoded_email, encoded_token)
    # If either is empty it should return False (line 117)
    self.assertFalse(self.manager.decrypt_link("", "token"))

    # Test line 115-117 branch if we can reach it
    # Actually decoded_email and decoded_token check is AFTER b64decode
    # So it's more about truthiness.

  def test_decrypt_link_failure_cases(self):
    # Test line 116-117
    # We need decoded_email or decoded_token to be falsy AFTER potential decoding
    # But b64decode of empty string is empty bytes.

    # To hit line 117 with logger.error
    # We need (decoded_email AND decoded_token) to be False.
    # This is tricky because b64decode('') is b'', which is falsy.
    encoded_email = urlsafe_b64encode(b"").decode("utf-8")
    result = self.manager.decrypt_link(encoded_email, "some-token")
    self.assertFalse(result)
