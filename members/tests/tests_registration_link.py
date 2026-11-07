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
    tampered_char = "1" if hash_val[-1] == "0" else "0"
    tampered_token = f"{ts}-{hash_val[:-1]}{tampered_char}"
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

    tenant_id, decrypted_email, name = self.manager.decrypt_link(encoded_email, token)
    self.assertEqual(decrypted_email, self.email)
    self.assertIsNone(tenant_id)  # link generated without a tenant
    self.assertIsNone(name)  # legacy link without a name

  def test_generate_and_decrypt_with_name(self):
    request = self.factory.get("/")
    link = self.manager.generate_link(request, self.email, tenant_id=3, name="John Doe")
    parts = link.split("/")
    reg_idx = parts.index("register")
    encoded_email, token = parts[reg_idx + 1], parts[reg_idx + 2]

    tenant_id, decrypted_email, name = self.manager.decrypt_link(encoded_email, token)
    self.assertEqual((tenant_id, decrypted_email, name), (3, self.email, "John Doe"))

  def test_decrypt_name_containing_colon(self):
    payload = f"{self.email}:Jean:Deaux"
    token = self.manager.make_token(payload)
    encoded_email = urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")
    _, email, name = self.manager.decrypt_link(encoded_email, token)
    self.assertEqual(email, self.email)
    self.assertEqual(name, "Jean:Deaux")

  def test_legacy_token_still_valid(self):
    # a token made before names existed (2-segment payload) must keep working
    legacy_payload = f"7:{self.email}"
    token = self.manager.make_token(legacy_payload)
    encoded_email = urlsafe_b64encode(legacy_payload.encode("utf-8")).decode("utf-8")
    tenant_id, email, name = self.manager.decrypt_link(encoded_email, token)
    self.assertEqual((tenant_id, email, name), (7, self.email, None))

  def test_check_invitation_with_name(self):
    token = self.manager.make_token(f"3:{self.email}:John Doe")
    self.assertTrue(self.manager.check_invitation(self.email, 3, token, name="John Doe"))
    self.assertFalse(self.manager.check_invitation(self.email, 3, token, name="Other Name"))
    self.assertFalse(self.manager.check_invitation(self.email, 3, token, name=None))

  def test_check_invitation_legacy_without_name(self):
    token = self.manager.make_token(self.email)
    self.assertTrue(self.manager.check_invitation(self.email, None, token, name=None))

  def test_decrypt_link_invalid_token(self):
    encoded_email = urlsafe_b64encode(self.email.encode("utf-8")).decode("utf-8")
    tenant_id, decrypted_email, name = self.manager.decrypt_link(encoded_email, "invalid-token")
    self.assertIsNone(decrypted_email)

  def test_decrypt_link_missing_data(self):
    # decrypt_link(self, encoded_email, encoded_token)
    # If either is empty it should return (None, None, None)
    tenant_id, decrypted_email, name = self.manager.decrypt_link("", "token")
    self.assertIsNone(decrypted_email)

  def test_decrypt_link_failure_cases(self):
    # b64decode('') is b'', which is falsy -> failure -> (None, None, None)
    encoded_email = urlsafe_b64encode(b"").decode("utf-8")
    tenant_id, decrypted_email, name = self.manager.decrypt_link(encoded_email, "some-token")
    self.assertIsNone(decrypted_email)
