"""Per-tenant settings lookup (branding + behavior keys).

The effective value for a key is: ``TenantSettings.overrides[key]`` for the
current tenant, else the global Django setting of the same (upper-case) name.
Keys are declared in ``TENANT_SETTINGS_SPEC``; anything not listed there is
never read per-tenant.
"""

from django.conf import settings as django_settings

from tenants.models import tenant_settings_overrides

# key -> name of the global Django setting used as the default value.
TENANT_SETTINGS_SPEC: dict[str, str] = {
  "site_name": "SITE_NAME",
  "site_logo": "SITE_LOGO",
  "site_copyright": "SITE_COPYRIGHT",
  "site_footer": "SITE_FOOTER",
  "pdf_size": "PDF_SIZE",
  "dark_mode": "DARK_MODE",
  "language_code": "LANGUAGE_CODE",
  "time_zone": "TIME_ZONE",
  "birthday_days": "BIRTHDAY_DAYS",
  "allow_members_to_create_members": "ALLOW_MEMBERS_TO_CREATE_MEMBERS",
  "allow_members_to_invite_members": "ALLOW_MEMBERS_TO_INVITE_MEMBERS",
  "family_chart_root_person_id": "FAMILY_CHART_ROOT_PERSON_ID",
}

# memoized per (tenant_id, spec-relevant globals); cleared by clear_tenant_settings_cache()
_cache: dict[tuple, dict] = {}


def clear_tenant_settings_cache():
  _cache.clear()


def _global_values() -> tuple:
  return tuple(getattr(django_settings, name, None) for name in TENANT_SETTINGS_SPEC.values())


def effective_overrides(tenant=None) -> dict:
  """All overrides of the (current) tenant, keyed by TENANT_SETTINGS_SPEC keys."""
  key = (getattr(tenant, "pk", "current"), _global_values())
  cached = _cache.get(key)
  if cached is None:
    cached = {k: v for k, v in tenant_settings_overrides(tenant).items() if k in TENANT_SETTINGS_SPEC}
    _cache[key] = cached
  return cached


def tenant_setting(key, default=None):
  """Effective value for ``key``: tenant override, else global setting, else ``default``."""
  setting_name = TENANT_SETTINGS_SPEC.get(key)
  if setting_name is None:
    raise KeyError(f"{key!r} is not a per-tenant setting")
  override = effective_overrides().get(key)
  if override is not None:
    return override
  if setting_name == "":
    return default
  global_value = getattr(django_settings, setting_name, None)
  return default if global_value is None else global_value
