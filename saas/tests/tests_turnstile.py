"""Turnstile verification tests: bypass flag, mocked siteverify outcomes."""

from unittest.mock import MagicMock, patch

from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from ..models import TenantRequest
from ..turnstile import verify_turnstile
from .utils import skip_if_saas_off


def _ok_response():
  resp = MagicMock()
  resp.json.return_value = {"success": True}
  return resp


def _ko_response():
  resp = MagicMock()
  resp.json.return_value = {"success": False}
  return resp


class TurnstileTests(TestCase):
  def setUp(self):
    skip_if_saas_off(self)

  def test_disabled_bypasses_verification(self):
    request = RequestFactory().post(reverse("saas:signup"), {})
    self.assertTrue(verify_turnstile(request))

  @override_settings(TURNSTILE_ENABLED=True, TURNSTILE_SECRET_KEY="secret")
  def test_success_accepts(self):
    request = RequestFactory().post(reverse("saas:signup"), {"cf-turnstile-response": "tok"})
    with patch("saas.turnstile.requests.post", return_value=_ok_response()) as post:
      self.assertTrue(verify_turnstile(request))
      self.assertEqual(post.call_args.kwargs["data"]["response"], "tok")

  @override_settings(TURNSTILE_ENABLED=True, TURNSTILE_SECRET_KEY="secret")
  def test_failure_refuses(self):
    request = RequestFactory().post(reverse("saas:signup"), {"cf-turnstile-response": "tok"})
    with patch("saas.turnstile.requests.post", return_value=_ko_response()):
      self.assertFalse(verify_turnstile(request))

  @override_settings(TURNSTILE_ENABLED=True, TURNSTILE_SECRET_KEY="secret")
  def test_network_down_fails_closed(self):
    request = RequestFactory().post(reverse("saas:signup"), {"cf-turnstile-response": "tok"})
    with patch("saas.turnstile.requests.post", side_effect=ConnectionError):
      self.assertFalse(verify_turnstile(request))

  @override_settings(TURNSTILE_ENABLED=True, TURNSTILE_SECRET_KEY="secret")
  def test_missing_token_refused_without_remote_call(self):
    request = RequestFactory().post(reverse("saas:signup"), {})
    with patch("saas.turnstile.requests.post") as post:
      self.assertFalse(verify_turnstile(request))
      post.assert_not_called()

  @override_settings(TURNSTILE_ENABLED=True, TURNSTILE_SECRET_KEY="secret")
  def test_signup_rejects_bad_captcha(self):
    with patch("saas.turnstile.requests.post", return_value=_ko_response()):
      resp = self.client.post(reverse("saas:signup"), {"tenant_name": "Smith", "email": "a@example.com"})
    self.assertRedirects(resp, reverse("saas:signup"))
    self.assertFalse(TenantRequest.objects.exists())
