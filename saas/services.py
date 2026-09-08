"""Business logic for tenant requests: creation, email, purge, schedule."""

import sys
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from .models import TenantRequest

# resolved requests are kept that long for platform support, then purged
RESOLVED_RETENTION = timedelta(days=30)


def create_tenant_request(email: str, tenant_name: str, ip: str | None = None) -> TenantRequest:
  """Store a new pending request whose expiry derives from SAAS_TENANT_REQUEST_MAX_AGE."""
  return TenantRequest.objects.create(
    email=email,
    tenant_name=tenant_name,
    ip=ip,
    expires_at=timezone.now() + timedelta(seconds=settings.SAAS_TENANT_REQUEST_MAX_AGE),
  )


def send_tenant_request_email(tenant_request: TenantRequest, link: str) -> None:
  """Render + send the verification email for a tenant request.

  The caller builds the absolute ``link`` (it needs the HTTP request); this
  function stays request-free.
  """
  msg = render_to_string(
    "saas/email/tenant_request_email.html",
    {
      "link": link,
      "tenant_name": tenant_request.tenant_name,
      "site_name": settings.SITE_NAME,
      "max_age_hours": settings.SAAS_TENANT_REQUEST_MAX_AGE // 3600,
    },
  )
  send_mail(
    _('Your new "%(name)s" family site on %(site_name)s')
    % {"name": tenant_request.tenant_name, "site_name": settings.SITE_NAME},
    strip_tags(msg),
    from_email=settings.DEFAULT_FROM_EMAIL,  # always use the default from email
    recipient_list=[tenant_request.email],
    html_message=msg,
  )


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
