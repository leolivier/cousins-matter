"""Tests for the superuser-only environment check page (core:env_check)."""

import redis
from smtplib import SMTPException
from unittest.mock import patch

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from core.services import run_env_checks
from members.tests.tests_member_base import MemberTestCase

ENV_CHECK_URL_NAME = "core:env_check"


class EnvCheckAccessTests(MemberTestCase):
  def _login_as_superuser(self):
    self.assertTrue(self.client.login(username=self.superuser.username, password=self.superuser.password))

  def test_superuser_gets_page(self):
    self._login_as_superuser()
    resp = self.client.get(reverse(ENV_CHECK_URL_NAME))
    self.assertEqual(resp.status_code, 200)
    checks = resp.context["checks"]
    self.assertGreaterEqual(len(checks), 8)
    for check in checks:
      self.assertEqual(set(check), {"name", "status", "label", "detail", "long_output"})
      self.assertIn(check["status"], ("ok", "warning", "error", "skipped"))
    self.assertContains(resp, "<table")

  def test_non_superuser_gets_403(self):
    # MemberTestCase.setUp logs self.member in
    resp = self.client.get(reverse(ENV_CHECK_URL_NAME))
    self.assertEqual(resp.status_code, 403)

  def test_anonymous_redirects_to_login(self):
    self.client.logout()
    resp = self.client.get(reverse(ENV_CHECK_URL_NAME))
    self.assertEqual(resp.status_code, 302)
    self.assertIn("login", resp["Location"])


class EnvCheckEmailTests(MemberTestCase):
  def setUp(self):
    super().setUp()
    self.assertTrue(self.client.login(username=self.superuser.username, password=self.superuser.password))

  def test_send_test_email(self):
    resp = self.client.post(reverse(ENV_CHECK_URL_NAME), {"action": "send_test_email"})
    self.assertRedirects(resp, reverse(ENV_CHECK_URL_NAME))
    self.assertEqual(len(mail.outbox), 1)
    self.assertEqual(mail.outbox[0].to, [self.superuser.email])

  @patch("core.services.send_mail", side_effect=SMTPException("SMTP server unreachable"))
  def test_send_test_email_failure_is_reported(self, _mock_send_mail):
    resp = self.client.post(reverse(ENV_CHECK_URL_NAME), {"action": "send_test_email"}, follow=True)
    self.assertEqual(resp.status_code, 200)
    self.assertContains(resp, "SMTP server unreachable")
    self.assertEqual(len(mail.outbox), 0)


class RunEnvChecksTests(MemberTestCase):
  @patch("core.services.redis_client")
  def test_run_env_checks_shape(self, _mock_redis):
    checks = run_env_checks()
    # one line per probe (two for db+redis), each with the full row shape
    self.assertEqual(
      {check["name"] for check in checks},
      {
        _("Database"),
        _("Redis"),
        _("Django-Q2 task queue"),
        _("Migrations"),
        _("Deployment checks"),
        _("Media storage"),
        _("Chat (Channels)"),
        _("Multi-tenancy"),
        _("Email"),
      },
    )
    for check in checks:
      self.assertEqual(set(check), {"name", "status", "label", "detail", "long_output"})
      self.assertIn(check["status"], ("ok", "warning", "error", "skipped"))

  @patch("core.services.redis_client")
  def test_probe_failure_is_isolated(self, _mock_redis):
    with patch("core.services._probe_django_q", side_effect=RuntimeError("boom")):
      checks = run_env_checks()
    errors = [check for check in checks if check["status"] == "error"]
    self.assertEqual(len(errors), 1)
    self.assertEqual(errors[0]["name"], _("Django-Q2 task queue"))
    self.assertIn("boom", errors[0]["detail"])
    # every other probe still reported, db probe unaffected
    db = next(check for check in checks if check["name"] == _("Database"))
    self.assertEqual(db["status"], "ok")

  @override_settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
  def test_dev_email_backend_is_a_warning(self):
    checks = run_env_checks()
    email = next(check for check in checks if check["name"] == _("Email"))
    self.assertEqual(email["status"], "warning")

  def test_redis_client_follows_settings(self):
    """redis_client must resolve REDIS_HOST through settings, not os.getenv defaults."""
    from core.services import redis_client
    from django.conf import settings

    self.assertEqual(redis_client.connection_pool.connection_kwargs.get("host"), settings.REDIS_HOST)

  def test_redis_down_reports_error_and_skips_django_q(self):
    with patch("core.services.redis_client") as mock_redis:
      mock_redis.ping.side_effect = redis.exceptions.ConnectionError("Error -2 connecting to redis:6379")
      checks = run_env_checks()
    redis_row = next(check for check in checks if check["name"] == _("Redis"))
    self.assertEqual(redis_row["status"], "error")
    self.assertIn("redis:6379", redis_row["detail"])
    q2 = next(check for check in checks if check["name"] == _("Django-Q2 task queue"))
    self.assertEqual(q2["status"], "skipped")
