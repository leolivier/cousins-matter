"""Purge command + schedule tests."""

from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from ..models import TenantRequest
from .utils import skip_if_saas_off


def _days_ago(dt, days):
  return dt - timedelta(days=days)


class PurgeTests(TestCase):
  def setUp(self):
    skip_if_saas_off(self)
    self.now = timezone.now()

  def _make(self, status, **fields):
    defaults = {
      "email": "a@example.com",
      "tenant_name": "Smith",
      "expires_at": self.now + timedelta(days=1),
    }
    defaults.update(fields)
    tr = TenantRequest.objects.create(status=status, **defaults)
    return tr

  def test_purge_keeps_fresh_and_removes_stale(self):
    fresh_pending = self._make(TenantRequest.Status.PENDING)
    stale_pending = self._make(TenantRequest.Status.PENDING, email="b@example.com", expires_at=_days_ago(self.now, 1))
    fresh_validated = self._make(
      TenantRequest.Status.VALIDATED,
      email="c@example.com",
      validated_at=self.now,
    )
    stale_validated = self._make(
      TenantRequest.Status.VALIDATED,
      email="d@example.com",
      validated_at=_days_ago(self.now, 31),
      expires_at=_days_ago(self.now, 30),
    )
    stale_expired = self._make(TenantRequest.Status.EXPIRED, email="e@example.com", expires_at=_days_ago(self.now, 31))

    call_command("purge_tenant_requests")

    remaining = set(TenantRequest.objects.values_list("email", flat=True))
    self.assertEqual(remaining, {fresh_pending.email, fresh_validated.email})
    self.assertFalse(TenantRequest.objects.filter(pk__in=[stale_pending.pk, stale_validated.pk, stale_expired.pk]).exists())
