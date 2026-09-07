"""Purge + schedule helpers for tenant requests."""

import sys
from datetime import timedelta

from django.utils import timezone

from .models import TenantRequest

# resolved requests are kept that long for platform support, then purged
RESOLVED_RETENTION = timedelta(days=30)


def purge_tenant_requests() -> int:
  """Delete stale requests: expired PENDING and resolved ones past retention."""
  now = timezone.now()
  deleted = 0
  expired_pending = TenantRequest.objects.filter(status=TenantRequest.Status.PENDING, expires_at__lt=now)
  deleted += expired_pending.delete()[0]
  for status, since in [
    (TenantRequest.Status.VALIDATED, "validated_at"),
    (TenantRequest.Status.EXPIRED, "expires_at"),
  ]:
    deleted += TenantRequest.objects.filter(status=status, **{f"{since}__lt": now - RESOLVED_RETENTION}).delete()[0]
  return deleted


def setup_purge_schedule():
  """Create the daily django-q2 purge schedule if absent (see saas.apps)."""
  # Do not run if we are migrating or testing or during one-off commands
  if any(arg in sys.argv for arg in ["makemigrations", "migrate", "test", "collectstatic"]):
    return
  from django_q.models import Schedule

  Schedule.objects.get_or_create(
    name="Purge expired tenant requests",
    defaults={
      "func": "saas.services.purge_tenant_requests",
      "schedule_type": Schedule.DAILY,
      "repeats": -1,  # forever
    },
  )
