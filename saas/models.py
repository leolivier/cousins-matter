"""Platform-level tenant requests for the SaaS signup flow.

``TenantRequest`` is NOT tenant-scoped: like ``Tenant`` it lives on the
platform tables and is created anonymously from the public site, before
any tenant exists. The signed validation link is HMAC stateless (see
tokens.py), so no token is stored.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TenantRequest(models.Model):
  """Anonymous request for a new family site, confirmed by signed email link."""

  class Status(models.TextChoices):
    PENDING = "pending", _("Pending")
    VALIDATED = "validated", _("Validated")
    EXPIRED = "expired", _("Expired")

  email = models.EmailField(_("Email"))
  tenant_name = models.CharField(_("Family name"), max_length=200)
  status = models.CharField(_("Status"), max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
  expires_at = models.DateTimeField(_("Expires at"))
  validated_at = models.DateTimeField(_("Validated at"), null=True, blank=True)
  ip = models.GenericIPAddressField(_("IP address"), null=True, blank=True)
  created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

  class Meta:
    verbose_name = _("tenant request")
    verbose_name_plural = _("tenant requests")
    ordering = ["-created_at"]

  def __str__(self):
    return f"{self.tenant_name} <{self.email}> ({self.status})"

  @property
  def is_pending(self) -> bool:
    return self.status == self.Status.PENDING

  @property
  def is_validated(self) -> bool:
    return self.status == self.Status.VALIDATED

  @property
  def is_expired(self) -> bool:
    return self.status == self.Status.EXPIRED

  @property
  def has_expired(self) -> bool:
    """The link validity window has passed, whatever the stored status."""
    return timezone.now() >= self.expires_at

  def mark_expired(self) -> None:
    self.status = self.Status.EXPIRED
    self.save(update_fields=["status"])
