"""Tenant models for the shared-schema multi-tenant architecture.

A ``Tenant`` represents one family/site served by the deployment. Every
tenant-scoped row carries a foreign key to it. Two tenants are seeded by the
data migration and are special:

* the **default** tenant (``DEFAULT_TENANT_SLUG``) — assigned to members when
  none can be resolved (e.g. management commands, legacy data);
* the **system** tenant (``SYSTEM_TENANT_SLUG``) — home of the platform
  (cross-tenant) superusers. It can never be deleted.

``TenantSettings`` holds per-tenant overrides (feature flags, branding) on top
of the global defaults.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

# Process-local memoization of the singleton tenants resolved by slug. These
# tenants are immutable after seeding, so the cache never needs invalidation.
_tenant_cache: dict[str, "Tenant"] = {}


def _reset_tenant_cache(**kwargs):
  """Drop memoized tenants.

  Needed for tests: TransactionTestCase truncates tables between tests, which
  invalidates memoized Tenant instances (their pks point at deleted rows and
  cause FK violations on later saves).
  """
  _tenant_cache.clear()


class Tenant(models.Model):
  name = models.CharField(_("Name"), max_length=200)
  slug = models.SlugField(_("Slug"), max_length=63, unique=True)
  is_active = models.BooleanField(_("Active"), default=True)
  created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
  updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

  class Meta:
    verbose_name = _("tenant")
    verbose_name_plural = _("tenants")
    ordering = ["name"]

  def __str__(self):
    return self.name

  @classmethod
  def _get_by_slug(cls, slug: str) -> "Tenant":
    cached = _tenant_cache.get(slug)
    if cached is not None:
      return cached
    # Bypass any future tenant scoping by using the plain manager.
    tenant = cls._base_manager.get(slug=slug)
    _tenant_cache[slug] = tenant
    return tenant

  @classmethod
  def get_default(cls) -> "Tenant":
    """The tenant assigned when none can be resolved (legacy/bootstrap data)."""
    return cls._get_by_slug(settings.DEFAULT_TENANT_SLUG)

  @classmethod
  def get_system(cls) -> "Tenant":
    """The tenant that hosts platform (cross-tenant) superusers."""
    return cls._get_by_slug(settings.SYSTEM_TENANT_SLUG)

  @property
  def is_system(self) -> bool:
    return self.slug == settings.SYSTEM_TENANT_SLUG


class TenantSettings(models.Model):
  tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="settings_row", verbose_name=_("Tenant"))
  # Feature-flag / branding overrides merged on top of the global defaults.
  overrides = models.JSONField(_("Overrides"), default=dict, blank=True)

  class Meta:
    verbose_name = _("tenant settings")
    verbose_name_plural = _("tenant settings")

  def __str__(self):
    return f"Settings for {self.tenant}"


def tenant_settings_overrides(tenant=None):
  """The ``overrides`` dict for ``tenant`` (default: the current tenant's).

  Returns ``{}`` when there is no tenant or no TenantSettings row — callers
  then fall back to the global Django settings.
  """
  from .scoping import get_current_tenant

  if tenant is None:
    tenant = get_current_tenant()
  if tenant is None:
    return {}
  tenant = tenant if isinstance(tenant, Tenant) else Tenant._base_manager.filter(pk=tenant.pk).first()
  if tenant is None:
    return {}
  settings_row = TenantSettings._base_manager.filter(tenant=tenant).only("overrides").first()
  return settings_row.overrides if settings_row and settings_row.overrides else {}


# Keep the memo in sync with the DB lifecycle: `flush` (run between
# TransactionTestCase tests) emits post_migrate, and override_settings emits
# setting_changed — both invalidate memoized tenant instances.
from django.core.signals import setting_changed  # noqa: E402
from django.db.models.signals import post_migrate  # noqa: E402

post_migrate.connect(_reset_tenant_cache, dispatch_uid="tenants.reset_cache.post_migrate")
setting_changed.connect(_reset_tenant_cache, dispatch_uid="tenants.reset_cache.setting_changed")


def _seed_tenants_post_migrate(**kwargs):
  """Re-create the default/system tenants after flush/migrate (idempotent).

  TransactionTestCase.flush wipes every table between tests, including the
  tenants seeded by the data migration (which only runs at migrate time).
  This keeps get_default()/get_system() working, the same way Django re-creates
  the default content types after a flush.
  """
  from django.conf import settings as dj_settings

  using = kwargs.get("using") or "default"
  if kwargs.get("apps") is not None:  # called as a data migration, not a signal
    return
  Tenant._base_manager.using(using).get_or_create(
    slug=dj_settings.DEFAULT_TENANT_SLUG,
    defaults={"name": "Default", "is_active": True},
  )
  Tenant._base_manager.using(using).get_or_create(
    slug=dj_settings.SYSTEM_TENANT_SLUG,
    defaults={"name": "System", "is_active": True},
  )


post_migrate.connect(_seed_tenants_post_migrate, dispatch_uid="tenants.seed_post_migrate")
