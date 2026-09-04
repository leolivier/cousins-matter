---
type: Conventions
title: Conventions
description: Repo-wide coding conventions — services pattern, custom user model, followers, feature flags, async and i18n
tags: [conventions, services, followers, feature-flags, i18n]
status: draft
stale_after: 2027-03-04
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T12:00:00Z }
---

# Conventions

## Business logic lives in services

Views stay thin; the business logic goes in `<app>/services.py`, or a `<app>/services/`
package when the app is big. Present today: `chat/services.py`, `classified_ads/services.py`,
`core/services.py`, `forum/services.py`, `galleries/services.py`, `genealogy/services.py`,
`polls/services.py`, `tenants/services.py`, and the `members/services/` package
(`members/services/members.py`, `members/services/directory.py`,
`members/services/import_export.py`). New code follows the same split.

## Custom user model

`AUTH_USER_MODEL = "members.Member"` (`config/settings/base.py`); `Member` extends
`AbstractUser` in `members/models.py`. Always resolve it with
`get_user_model()` — never import `Member` directly in reusable code.

## Followers drive notifications

`core/followers.py` implements member-to-object following: `toggle_follow` to follow/unfollow,
`check_followers` / `do_check_followers` to collect the followers of a followed object, and
`generate_emails` to build the notification emails when something new is posted on a followed
object. Apps call these utilities (possibly through a Django-Q2 task) instead of
reimplementing notification fan-out. Details in [/modules/followers.md](/modules/followers.md)
and [/modules/notifications.md](/modules/notifications.md).

## Feature flags

`FEATURES_FLAGS` in `config/settings/base.py` is an `env.dict` of booleans
(`show_galleries`, `show_forums`, `show_public_chats`, `show_private_chats`,
`show_classified_ads`, `show_polls`, `show_event_planners`, `show_pages`, `show_treasures`,
`show_genealogy`, `show_birthdays_in_homepage`, `show_site_stats`,
`show_export_members`, `show_change_language`, ...). It is surfaced to templates by the
`featured` filter in `core/templatetags/cm_tags.py` (`{% load cm_tags %}` then
`{{ "show_galleries"|featured }}`), which layers per-tenant overrides from
`TenantSettings.overrides` on top of the global dict and memoizes the merge
(`clear_flags_cache()` invalidates it). Note: the `settings()` context processor in
`core/context_processors.py` exposes the `EXPOSED_SETTINGS` list, not the feature flags.
Details in [/modules/feature-flags.md](/modules/feature-flags.md).

## Async via Django-Q2

Anything slow (emails, notifications, bulk imports) runs as a Django-Q2 task
(`django-q2` in `pyproject.toml`). `Q_CLUSTER` is configured in `config/settings/base.py`
against Redis, with `"sync": env.bool("Q_SYNC", False)`; `config/settings/dev_base.py`
defaults `Q_SYNC` to `True` for `development`, `docker-devt` and `test` settings, so tasks
execute synchronously and can be debugged/tested without a broker round-trip. Schedules live
in `core/tasks_schedules.py`.

## Translations (i18n)

`USE_I18N = True` and six locales in `LANGUAGES` (`config/settings/base.py`): fr, en, es, de,
it, pt. Workflow per app:

- `make mkmsg a=<app>` — `makemessages -a` inside the app (`Makefile`)
- `make cpmsg a=<app>` — `compilemessages` inside the app

`LANGUAGE_CODE` defaults to `en`. The user-facing workflow is documented in the
[user manual translations page](https://cousins-matter.readthedocs.io/translations/).

## Templates, settings exposure and theming

`core/context_processors.py` exposes a curated `EXPOSED_SETTINGS` list as `settings` in
templates, with per-tenant overrides applied on top (`tenants/settings_overrides.py`). Tests
must use `core.context_processors.override_settings`, which also recomputes the exposed dict.
Theming/customization (logo, footer, `theme.css`) is covered in
[/modules/themes.md](/modules/themes.md) and the
[user manual customizing page](https://cousins-matter.readthedocs.io/customizing/).

# See also

- [Architecture](/architecture.md) — settings, middleware, serving
- [Development Setup](/setup-dev.md)
- [Testing](/testing.md)
- Modules: [followers](/modules/followers.md), [notifications](/modules/notifications.md),
  [feature flags](/modules/feature-flags.md), [themes](/modules/themes.md)
- User manual: [translations](https://cousins-matter.readthedocs.io/translations/),
  [customizing](https://cousins-matter.readthedocs.io/customizing/)
