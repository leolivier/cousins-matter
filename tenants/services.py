"""Tenant lifecycle services (shared by the management UI and the command)."""

import logging

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from .models import Tenant

logger = logging.getLogger(__name__)


def delete_tenant(tenant: Tenant) -> int:
  """Hard-delete ``tenant`` and all its data; returns the member count removed.

  Refuses the system tenant (never deletable) and any still-active tenant —
  deactivation must happen first so the action stays deliberate.
  ``Member.tenant`` is ``on_delete=PROTECT``, so members are removed explicitly
  before the tenant; tenant-scoped rows (galleries, photos) cascade.
  """
  from members.models import Member

  if tenant.is_system:
    raise PermissionDenied(_("The system tenant cannot be deleted."))
  if tenant.is_active:
    raise PermissionDenied(_("This family is still active. Deactivate it before deleting it."))

  member_count = Member.unscoped.filter(tenant=tenant).count()
  Member.unscoped.filter(tenant=tenant).delete()
  name, slug = tenant.name, tenant.slug
  tenant.delete()  # cascades tenant-scoped rows (galleries, photos)
  logger.info(f"Deleted tenant {name!r} ({slug!r}) and {member_count} member(s).")
  return member_count
