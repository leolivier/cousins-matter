---
type: Module Reference
title: Feature Flags
description: FEATURES_FLAGS defaults, the |featured template filter, per-family overrides through TenantSettings.overrides, and how to add a new flag
tags: ["module", "feature-flags"]
status: draft
stale_after: 2027-05-22
generated: { by: claude-code/glm-5.3-flash, at: 2026-11-22T12:22:29Z }
---

# Feature Flags

Feature flags are plain booleans with a global default, an env override, and
an optional per-family override. There is no flag service and no database
table for them — the per-family layer reuses `TenantSettings.overrides`.

## Global defaults

`FEATURES_FLAGS` (config/settings/base.py) is an `env.dict(...,
cast={"value": bool})`, so the whole dict can be replaced from the
environment. The shipped keys, all `True` by default:

`show_birthdays_in_homepage`, `show_galleries`, `show_forums`,
`show_public_chats`, `show_private_chats`, `show_classified_ads`,
`show_polls`, `show_event_planners`, `show_pages`, `show_treasures`,
`show_site_stats`, `show_export_members`, `show_change_language`,
`show_genealogy`.

## Surfacing

- The `featured` filter (core/templatetags/cm_tags.py) resolves the current
  tenant from thread-local state (set by `tenants.middleware.TenantMiddleware`
  via `tenants.scoping.get_current_tenant`) and returns the flag value,
  defaulting to `False` for unknown keys:
  `{% if 'show_galleries'|featured %}` (core/templates/core/navbar.html).
- Resolution order in `_feature_flags(tenant)`: global `FEATURES_FLAGS`
  values, then `TenantSettings.overrides` for that tenant merged on top —
  any overrides key whose name matches a flag wins for that family. Result is
  memoized per process in `_tenant_flags_cache`, keyed by (tenant pk, global
  flags tuple) so test `override_settings(FEATURES_FLAGS=...)` invalidates
  naturally.
- `TenantSettings.save()` invalidates both memos: the tenant-settings memo is
  versioned through the shared cache (every process recomputes), and
  `clear_flags_cache()` drops the local flags memo. This covers the family
  settings form, the Django admin and direct ORM edits
  ([Tenants](/apps/tenants.md#per-tenant-settings-tenantssettings_overridespy)).
- The flags memo itself is still per process. That is accepted because
  `|featured` is only evaluated while rendering templates in daphne (a single
  process, `Dockerfile:54`); qcluster never renders templates. If a second web
  worker is added, give it the same version-key treatment as the tenant
  settings.
- The family settings UI (`tenants:settings` →
  tenants/views/views_settings.py) only exposes the branding/behavior keys of
  `TENANT_SETTINGS_SPEC`, not flags: per-family flag overrides are set
  through the Django admin on the `TenantSettings` row.

## Adding a flag

1. Add the key with its default to the `FEATURES_FLAGS` dict in
   config/settings/base.py (operators can flip it globally via the
   `FEATURES_FLAGS` env dict).
2. Gate the template/code with `'my_flag'|featured` — unknown flags are
   falsy, so a typo hides the feature silently.
3. Optionally, for a per-family toggle, set the same key in a
   `TenantSettings.overrides` row and it overrides the default for that
   family only.

Flags are about *visibility* (menu entries, home-page blocks); branding and
behavior knobs (`dark_mode`, `birthday_days`, ...) are per-tenant *settings*
instead — [Themes & Customization](/modules/themes.md).

# See also

- [Core](/apps/core.md#feature-flags-and-context-processors) — `featured`
  implementation and `EXPOSED_SETTINGS`.
- [Tenants](/apps/tenants.md#per-tenant-settings-tenantssettings_overridespy).
- [Conventions](/conventions.md#feature-flags).
- User manual: features management at
  <https://cousins-matter.readthedocs.io/customizing/>.
