---
type: App Reference
title: Core
description: Site-wide plumbing — NotificationEvent, contact form, site stats, protected media, followers batching, feature flags, context processors, management commands
tags: ["app", "core"]
status: draft
stale_after: 2027-03-04
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T12:00:00Z }
---

# Core

`core` is the grab-bag app for cross-app plumbing: the settings entry point,
the home/about/contact pages, health checks, protected media downloads, the
generic follow/notification machinery, feature flags, template helpers and the
test-data management commands. It has a single domain model,
`NotificationEvent`; everything else is views, services and templatetags.

## Model: NotificationEvent

`NotificationEvent` (core/models.py) is one pending notification for one
member: generic FKs to the *followed* object and the *new* object that
triggered it, the `author`, a `followed_object_url` and `created_at`.
Rows are created by `core.followers.do_check_followers` for members whose
`email_batch_frequency` is neither `never` nor `immediate`, consumed (and
deleted) by the batch job below.

## URLs and views

`core/urls.py` (`app_name = "core"`, mounted at the root by
cousinsmatter/urls.py):

- `/` — `HomeView`, a `TemplateView` on `core/base.html`.
- `/contact/` — `ContactView` (core/views/views_contact.py), a `FormView` on
  `ContactForm`; the recipient is `tenants.authz.admin_or_superusers()` for the
  current tenant, falling back to the first platform superuser, and sending is
  delegated to `do_send_contact_email` (core/services.py), which builds a
  multipart email with the optional uploaded attachment.
- `/about/` — `statistics` (core/views/views_stats.py): `get_latest_release_text`
  queries the GitHub API for the latest release and compares it with
  `settings.APP_VERSION` (reporting "not up-to-date" through the messages
  framework), then `build_site_stats(site_url, release_text)`
  (core/services.py) counts members/galleries/forum/chat objects for the
  current tenant and renders `core/about/site-stats.html`.
- `/jsi18n/core/<lang>` — `JavaScriptCatalog`, `last_modified`-cached.

Infrastructure endpoints (cousinsmatter/urls.py): `health` and `qhealth`
(login not required) both call `health_check` (core/services.py) — a
`SELECT 1` on the database plus a Redis `PING` — the latter running it through
Django-Q to prove the broker works.

## Protected media

`download_protected_media` and `download_public_media`
(core/views/views_general.py) are mounted at `settings.MEDIA_URL` and
`settings.PUBLIC_MEDIA_URL` in cousinsmatter/urls.py — media is **never**
served by the web server directly. Both stream in 64 KB chunks from
`default_storage` and answer `If-None-Match` with a blake2b ETag built from
`"<username>@<media>"`. The public variant is decorated `@login_not_required`
and prefixes `public/` (i.e. `PUBLIC_MEDIA_ROOT = MEDIA_ROOT / "public"`,
config/settings/base.py); the protected one requires login through
`core.middleware.LoginRequiredMiddleware` (below). Helper:
`protected_media_url` (core/utils.py).

## Followers and notification batching

Generic following of *any* model lives in core/followers.py:

- `check_followers(request, followed_object, owner, url, new_object, author)`
  makes the URL absolute and dispatches `do_check_followers` as a Django-Q
  task (`async_task`), passing `tenant_id` explicitly because the worker has
  no request/middleware; `post_check_followers` is the hook.
- `do_check_followers` runs inside `tenant_context(...)` (tenants/scoping.py),
  collects recipients from `followed_object.followers` plus the owner's and
  author's own followers, drops the author, then splits:
  `FREQUENCY_NEVER` → skipped; `FREQUENCY_IMMEDIATE` → emailed now via
  `generate_emails`; anything else → one `NotificationEvent` row per recipient.
- `toggle_follow(request, followed_object, owner, url)` is the follow/unfollow
  entry point used by content apps.

The batch job `process_batched_notifications(frequency)` (core/tasks.py)
selects the pending events of every member whose
`email_batch_frequency == frequency`, groups them per member, renders
`core/followers/email-notification-summary.html` (with
`tenant_setting("site_name")`), sends one digest email, then deletes the
events. It is scheduled by `setup_notification_schedules`
(core/tasks_schedules.py): hourly/daily/weekly/monthly Django-Q `Schedule`
rows (monthly falls back to cron `"0 0 1 * *"` on Django-Q versions without
`Schedule.MONTHLY`), created `get_or_create` so manual admin edits survive.
`core/apps.py` connects it to `post_migrate`; the handler no-ops during
`migrate`/`test`/`collectstatic`.

See [Followers](/modules/followers.md) for the end-to-end flow.

## Feature flags and context processors

Global flags come from `FEATURES_FLAGS` (an `env.dict` with a `show_*`
boolean default, config/settings/base.py). Their resolution is **template
side**, not a context processor:

- the `featured` filter (core/templatetags/cm_tags.py) returns whether the
  flag is on, honouring per-tenant overrides: `_feature_flags(tenant)` merges
  the global dict with the current tenant's `TenantSettings.overrides` and
  memoizes the result in `_tenant_flags_cache`;
  `clear_flags_cache()` invalidates it (call it after editing
  `TenantSettings.overrides`). Templates use it as e.g.
  `{% if 'show_galleries'|featured %}` (core/templates/core/navbar.html).
- `core.context_processors.settings` exposes the settings listed in
  `EXPOSED_SETTINGS` to templates as `{{ settings.X }}`, with the current
  tenant's overrides from `tenants.settings_overrides.effective_overrides`
  layered on top (e.g. per-family `SITE_NAME`, `DARK_MODE`,
  `BIRTHDAY_DAYS`). `recompute_settings_in_templates()` refreshes the
  memoized global dict, and the `override_settings` subclass re-computes it so
  tests see template-visible changes.

## Middleware

`core.middleware.LoginRequiredMiddleware` extends Django's
`LoginRequiredMiddleware` and exempts every path prefix in
`LOGIN_REQUIRED_IGNORE_PATHS` (allauth/OAuth callbacks must stay reachable
while anonymous). It sits right after `tenants.middleware.TenantMiddleware` in
`MIDDLEWARE` (config/settings/base.py) — see
[Architecture](/architecture.md).

Also in core: `core.mixins` (`LoginNotRequiredMixin`, `OnlyAdminMixin`) and
`core.utils` (paginator, thumbnails `create_thumbnail` /
`create_video_thumbnail`, date parsing helpers `parse_locale_date`,
`storage_rmtree`, `confirm_delete_modal`, ...).

## Management commands

- `generate_test_data` (core/management/commands/generate_test_data.py) —
  for each app (or `--app`), imports `<app>/tests/factories.py`, instantiates
  `--count` objects per factory and dumps them as fixtures into the app's
  resources folder.
- `import_test_data` (core/management/commands/import_test_data.py) —
  `loaddata`s `<app>/tests/resources/fixtures.json` per app, in FK-friendly
  order (members first).
- `check_okf` — validates the frontmatter of this documentation bundle (see
  [Conventions](/conventions.md)).

# See also

- [Members](/apps/members.md) — `Member.email_batch_frequency`, managed members
- [Tenants](/apps/tenants.md) — `TenantSettings.overrides` behind flags and `tenant_setting`
- [Followers](/modules/followers.md) — the follow/notification flow
- [Architecture](/architecture.md) — settings entry point, middleware order
- user-manual/settings.md — feature-flag and per-tenant settings from an admin's perspective
