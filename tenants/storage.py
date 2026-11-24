"""Tenant-aware media storage helpers.

With ``MULTI_TENANT_ENABLED`` on, every protected upload lives under
``<media root>/<tenant slug>/`` so two families can never collide on disk and
the download view can scope files by their first path segment. With the flag
off (self-hosted mono-tenant) the helpers are a no-op: paths stay exactly as
they were before tenancy.
"""

import logging
import os

from django.conf import settings
from django.core.files.base import ContentFile

from tenants.models import Tenant
from tenants.scoping import get_current_tenant

logger = logging.getLogger(__name__)


def tenant_prefix(instance) -> str:
  """Tenant slug that prefixes the instance's upload path, or "" when mono-tenant.

  With MULTI_TENANT_ENABLED off, upload paths must be exactly what they were
  before this change, so no prefix and no tenant query. Otherwise this mirrors
  ``TenantModel.ensure_tenant()``: the instance's own tenant, else the active
  tenant, else the seeded default tenant (commands, factories, in-memory
  objects saved outside a request).
  """
  if not settings.MULTI_TENANT_ENABLED:
    return ""
  tenant = getattr(instance, "tenant", None)  # safe: an unset FK raises AttributeError
  if tenant is None:
    tenant = get_current_tenant() or Tenant.get_default()
  return tenant.slug


def tenant_path(instance, *parts) -> str:
  """Join the instance's tenant prefix with a relative storage path."""
  # os.path.join("", "galleries", ...) == "galleries/...": flag-off is a no-op
  return os.path.join(tenant_prefix(instance), *parts)


def move_file(storage, old_name: str, new_name: str) -> bool:
  """Move one file with the generic Storage API (filesystem or remote). Returns True on success."""
  try:
    if not storage.exists(old_name):
      return False
    if storage.exists(new_name):
      storage.delete(new_name)
    with storage.open(old_name, "rb") as f:
      content = f.read()
    storage.save(new_name, ContentFile(content))
    try:
      storage.delete(old_name)
    except Exception as e:
      # a duplicate left behind is harmless: the DB name is the new one
      logger.warning("Failed to delete old file %s: %s", old_name, e)
    return True
  except Exception as e:
    logger.warning("Failed to move file %s -> %s: %s", old_name, new_name, e)
    return False
