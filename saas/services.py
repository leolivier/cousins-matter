"""Business logic for tenant requests: creation, validation, email, purge, schedule."""

import sys
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from members.models import Member
from pages.services import seed_tenant_pages
from tenants.forms import uniquify_tenant_slug
from tenants.models import Tenant, TenantSettings

from .models import TenantRequest
from .tokens import TenantRequestTokenManager

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


def resolve_tenant_request(encoded: str, token: str) -> TenantRequest | None:
  """Return the request of a valid, pending, unexpired signed link, else None.

  A pending-but-expired request gets marked EXPIRED (the link was replayed
  after the window); other failures leave the request untouched.
  """
  tenant_request = TenantRequestTokenManager().decrypt_link(encoded, token)
  if tenant_request is None:
    return None
  if tenant_request.is_pending and tenant_request.has_expired:
    tenant_request.mark_expired()
  if not tenant_request.is_pending or tenant_request.has_expired:
    return None
  return tenant_request


def create_tenant_from_request(tenant_request: TenantRequest) -> Member:
  """Fulfil a pending request: Tenant + TenantSettings + active admin Member.

  The slug is computed at creation time (automatic ``-2`` suffix on
  collision) and the request is marked VALIDATED in the same transaction.
  Raises on failure (no free slug, duplicate username, ...), rolling
  everything back.
  """
  with transaction.atomic():
    slug = uniquify_tenant_slug(tenant_request.tenant_name)
    tenant = Tenant.objects.create(name=tenant_request.tenant_name, slug=slug)
    TenantSettings.objects.create(tenant=tenant)
    # the family gets its own editable copy of the predefined pages
    seed_tenant_pages(tenant)
    username = tenant_request.email.partition("@")[0]
    member = Member.unscoped.create(
      username=username,
      email=tenant_request.email,
      tenant=tenant,
      role=Member.Role.ADMIN,
      is_active=True,
    )
    # password chosen on the welcome screen right after auto-login
    member.set_unusable_password()
    member.save()
    tenant_request.status = TenantRequest.Status.VALIDATED
    tenant_request.validated_at = timezone.now()
    tenant_request.save(update_fields=["status", "validated_at"])
  return member


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
