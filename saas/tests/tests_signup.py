"""Tenant request flow tests: form, throttle, member-email refusal (Turnstile off)."""


from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from members.models import Member
from tenants.models import Tenant

from ..models import TenantRequest
from .utils import skip_if_saas_off


class SignupTests(TestCase):
  def setUp(self):
    skip_if_saas_off(self)
    cache.clear()  # throttle state

  def _post(self, email="founder@example.com", name="Smith"):
    return self.client.post(reverse("saas:signup"), {"tenant_name": name, "email": email})

  def test_get_shows_form(self):
    resp = self.client.get(reverse("saas:signup"))
    self.assertEqual(resp.status_code, 200)
    self.assertContains(resp, "email")

  def test_valid_request_creates_pending_and_sends_mail(self):
    resp = self._post()
    self.assertRedirects(resp, reverse("saas:signup_sent"))
    tr = TenantRequest.objects.get(email="founder@example.com")
    self.assertEqual(tr.status, TenantRequest.Status.PENDING)
    self.assertEqual(tr.tenant_name, "Smith")
    delta = (tr.expires_at - timezone.now()).total_seconds()
    self.assertAlmostEqual(delta, 24 * 3600, delta=10)
    self.assertEqual(len(mail.outbox), 1)
    # the signed link is in the HTML alternative (plain part strips tags)
    html = mail.outbox[0].alternatives[0][0]
    self.assertIn("/saas/validate/", html)
    # nothing is created before the link is clicked (default/system tenants
    # are seeded on every deployment, hence the slug filter)
    self.assertFalse(Tenant.objects.exclude(slug__in=["default", "system"]).exists())

  def test_existing_member_email_refused(self):
    Member.objects.create(username="founder", email="founder@example.com")
    resp = self._post()
    self.assertEqual(resp.status_code, 200)
    self.assertContains(resp, "already exists")
    self.assertFalse(TenantRequest.objects.exists())

  def test_throttled_after_5_posts_per_hour(self):
    for _ in range(5):
      self._post(email=f"ok{timezone.now().microsecond}@example.com")
    resp = self._post(email="sixth@example.com")
    self.assertRedirects(resp, reverse("saas:signup"))
    self.assertFalse(TenantRequest.objects.filter(email="sixth@example.com").exists())
