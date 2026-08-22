"""Multi-tenant scoping primitives (shared-schema approach).

A thread-local holds the "current tenant". `TenantManager` filters every
queryset by it; `TenantModel` auto-assigns it on save. `tenant_context()`
activates a tenant in background workers, management commands and tests,
where no HTTP request is available to set it via middleware.

This is the active isolation layer. PostgreSQL row-level security (enabled
inert in migrations) is a backstop that activates once a non-owner DB role
is introduced.
"""

import threading
from collections.abc import Iterator
from contextlib import contextmanager

from django.db import models

_thread_locals = threading.local()


def get_current_tenant():
  """Return the tenant active for the current thread, or None when unset."""
  return getattr(_thread_locals, "tenant", None)


def set_current_tenant(tenant) -> None:
  """Set (or clear, when None) the current thread's tenant."""
  _thread_locals.tenant = tenant


@contextmanager
def tenant_context(tenant) -> Iterator[None]:
  """Activate ``tenant`` within a block, restoring the previous value on exit.

  Use in Django-Q workers, management commands and tests where no request
  sets the current tenant through middleware. Also drives the RLS session
  variable when the runtime role is configured (see tenants/rls.py).
  """
  from .rls import reset_rls, set_rls_tenant

  previous = get_current_tenant()
  set_current_tenant(tenant)
  set_rls_tenant(tenant.pk if tenant is not None else None)
  try:
    yield
  finally:
    set_current_tenant(previous)
    reset_rls()


class TenantManager(models.Manager):
  """Manager that filters querysets by the current tenant.

  When no tenant is active (anonymous request, management command, platform
  superuser), the queryset is left unfiltered so that authentication lookups,
  ``createsuperuser`` and migrations keep working. Use the model's ``unscoped``
  manager for explicit cross-tenant access (admin views, billing, exports).
  """

  def get_queryset(self):
    qs = super().get_queryset()
    tenant = get_current_tenant()
    if tenant is not None:
      qs = qs.filter(tenant=tenant)
    return qs


class TenantModel(models.Model):
  """Abstract base for tenant-scoped models.

  Subclasses get a non-editable ``tenant`` FK, a scoped ``objects`` manager,
  an ``unscoped`` escape-hatch manager, and auto-assignment of the current
  tenant on save (raising if none can be resolved).

  Note: ``Member`` deliberately does NOT inherit this class — it owns the
  tenant FK that identifies the tenant, so it redeclares ``tenant`` itself
  with its own (permissive) save() fallback.
  """

  tenant = models.ForeignKey(
    "tenants.Tenant",
    on_delete=models.CASCADE,
    editable=False,
    related_name="+",
  )

  objects = TenantManager()
  unscoped = models.Manager()

  class Meta:
    abstract = True

  def ensure_tenant(self):
    """Resolve and set the tenant from the current thread if not already set.

    Raises if no tenant can be resolved. Subclasses that override ``save`` and
    call ``full_clean()`` before ``super().save()`` should call this first, so
    the (non-nullable) tenant passes field validation.
    """
    if self.tenant_id is None:
      tenant = get_current_tenant()
      if tenant is None:
        raise ValueError(
          "Cannot save a tenant-scoped model without a current tenant; "
          "wrap the call in tenant_context(...) or set an explicit tenant."
        )
      self.tenant = tenant

  def save(self, *args, **kwargs):
    self.ensure_tenant()
    super().save(*args, **kwargs)
