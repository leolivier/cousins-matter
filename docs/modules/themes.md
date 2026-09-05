---
type: Module Reference
title: Themes & Customization
description: Per-family branding (name, logo, footer, copyright, dark mode) through tenant settings, plus the theme.css stylesheet served from public media
tags: ["module", "themes"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T11:16:06Z }
---

# Themes & Customization

Customization has two layers: per-family *settings* (branding strings and
booleans stored in `TenantSettings.overrides`) and one global *stylesheet*
(`media/public/theme.css`) for real look-and-feel changes. Both are
operator-facing — the user manual is the reference for "how do I change my
site".

## Per-family branding

- The editable keys are those of `TENANT_SETTINGS_SPEC`
  (tenants/settings_overrides.py): `site_name`, `site_logo`,
  `site_copyright`, `site_footer`, `pdf_size`, `dark_mode`, `language_code`,
  `time_zone`, `birthday_days`, `allow_members_to_create_members`,
  `allow_members_to_invite_members`, `family_chart_root_person_id`.
- The family settings page (`tenants:settings`,
  tenants/views/views_settings.py) builds its form from that spec, shows the
  *effective* values (override if set, else the global Django setting), and
  stores only the deltas in `TenantSettings.overrides`; it then clears the
  tenant-settings and feature-flag caches.
- Templates read them through the `settings` context processor
  (core/context_processors.py): a curated `EXPOSED_SETTINGS` list exposed as
  `{{ settings.X }}`, with the current tenant's overrides layered on top by
  `tenants.settings_overrides.effective_overrides` — e.g.
  `{{ settings.SITE_FOOTER }}`, `{{ settings.SITE_COPYRIGHT }}`.
- `DARK_MODE` toggles Bulma's dark theme:
  core/templates/core/base.html renders `data-theme="dark"` when
  `{{ settings.DARK_MODE }}` is truthy.

## CSS assets

- `core/templates/core/base.html` loads
  `{{ settings.PUBLIC_MEDIA_URL }}theme.css`, i.e.
  `/public_media/theme.css`, served anonymously from the public storage
  ([Protected Media](/modules/protected-media.md)). The file must therefore
  live in `media/public/`.
- `theme.css` is the customization hook: set Bulma CSS variables there (the
  shipped `media/public/theme.css` stub shows a `:root` example overriding
  `--bulma-primary-*`). In Docker the `./media:/app/media` volume
  (docker-compose.yml) keeps it editable from the host, and the container
  entrypoint (scripts/entrypoint.py) documents creating the media tree and
  `theme.css` on first run.
- Static assets themselves (Bulma, app CSS/JS) are WhiteNoise-served and not
  meant to be edited per deployment
  ([Architecture](/architecture.md#static-and-media)).

Quick decision guide: rename the family or change its footer → tenant
settings page; change colors/fonts → `theme.css`; hide a whole feature →
[Feature Flags](/modules/feature-flags.md).

# See also

- [Tenants](/apps/tenants.md#per-tenant-settings-tenantssettings_overridespy)
  — overrides storage and caching.
- [Core](/apps/core.md#feature-flags-and-context-processors) —
  `EXPOSED_SETTINGS` and `settings` in templates.
- [Protected Media](/modules/protected-media.md) — why `theme.css` lives in
  public media.
- [Conventions](/conventions.md#templates-settings-exposure-and-theming).
- User manual: <https://cousins-matter.readthedocs.io/customizing/>
  (Settings, Custom footer, Themes sections).
