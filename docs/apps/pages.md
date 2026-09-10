---
type: App Reference
title: Pages
description: Pages app (`pages`) — minimal CMS on top of django.contrib.flatpages, with publish/private URL conventions, menu/tree template tags and a predefined-pages import; documented in apps/pages.md
tags: ["app", "pages"]
status: draft
stale_after: 2027-03-10
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-10T00:00:00Z }
---

# Pages

`pages` is the basic CMS: it subclasses
`django.contrib.flatpages.FlatPage` and adds the bookkeeping needed to
ship editable pages (menu entries, an "about" tree, homepage blocks)
without losing admin-managed defaults. Pages are served by the
tenant-aware `pages.views.flatpage` view at
`<PAGES_URL_PREFIX><url>` (cousinsmatter/urls.py) and, on 404s, by
`pages.middleware.TenantFlatpageFallbackMiddleware`
(config/settings/base.py) — both scoped replacements for
django.contrib.flatpages' global-table versions.

**Redirect guard:** the `APPEND_SLASH` 301 emitted by
`pages.views.flatpage` is built from `request.path`, which is
user-controlled; since the model has no url validator (only
`PageForm` regex-validates), a planted page whose url is
protocol-relative (`//host/x/`, `/\host/x/`) would turn any 404 into
a redirect off-site (CWE-601). The redirect target is therefore
checked with `url_has_allowed_host_and_scheme` and an invalid target
raises `Http404` (pages/tests/tests_flatpage_redirect.py).

**Tenant note:** `FlatPage` is a [TenantModel](/apps/tenants.md) (MTI
child: the `tenant` column lives on `pages_flatpage`, the contrib
parent table `django_flatpage` stays global). Its global `url` unique
was dropped in `pages.0004_tenant` so every family can own
`/home/authenticated/`; per-tenant URL uniqueness is enforced by the
scoped `PageForm`. Each new tenant gets its own copy of the
predefined pages via `pages.services.seed_tenant_pages`, called from
the signup and `TenantCreateView` flows.

## Model (pages/models.py)

- `FlatPage(TenantModel, _FlatPage)` — everything from contrib flatpages (`url`,
  `title`, `content`, `registration_required`, `sites` M2M), plus:
  - `predefined` — the page was imported from the predefined
    fixtures rather than created in the UI;
  - `updated` — the page was created or edited in the UI since the
    last import (defaults `True`, i.e. "treat as hand-edited").
- `create_page(url, title, content)` helper: creates the page and
  attaches the current `SITE_ID` — a page not linked to a site is
  never served by the flatpages fallback.

## Publication workflow (URL conventions)

Publication is driven by the page **URL prefix**, not a boolean flag:

- `/publish/...` (`MENU_PAGE_URL_PREFIX`) — public pages, rendered as
  the navbar menu by the `pages_menu` tag.
- `/private/...` (`PRIVATE_PAGE_URL_PREFIX`) — private pages, shown in
  a separate "Private" section; combine with flatpages'
  `registration_required` to demand login.
- Both are surfaced to templates by `context_processors`
  (core/context_processors.py).

`build_pages_tree` (pages/templatetags/pages_tags.py) turns the flat
url list into a nested dict keyed by path segments (leaves are page
objects), filtered by prefix and — unless the viewer is privileged —
with `predefined=False`. The `pages_tree` tag includes predefined
pages only for superusers and tenant admins, so half-translated
stock pages never leak to members.

## Editing (admin publication workflow)

Two URL namespaces, one app (`app_name = "pages-edit"`):

- Public read side: `pages-edit:tree` (`PageTreeView`) renders the
  page tree for any visitor.
- Admin side, gated twice: views use
  `core.mixins.OnlyAdminMixin` (superuser **or** tenant admin) and
  the create/update/delete `post` handlers re-check
  `request.user.is_superuser` and raise `PermissionDenied` otherwise —
  the tightest rule in the app wins.
  - `edit_list` (`PageAdminListView`) — flat list with sites.
  - `create` / `<pk>` — `PageForm` save wrapped in
    `transaction.atomic()` with the site association and the
    `updated=True` flag: an unflagged edit can never be silently
    overwritten by a later import. Buttons: `save` (redirect to the
    page) or `save-and-continue`.
  - `<pk>/delete` — HTMX confirm modal, then redirect to the list.

## Predefined pages import

pages/fixtures/predefined_flatpages.json holds stock pages
(homepage, about, charter…). pages/migrations/0002_import_predefined_pages.py
imports them idempotently:

- a predefined page that exists and is **not** `updated` is refreshed
  from the fixture;
- one that was edited in the UI (`updated=True`) is **skipped** — UI
  edits win;
- pre-existing non-predefined flatpages are converted with
  `predefined=False, updated=True`.

The same logic is what the `updated` flag protects on later re-imports.
The fixture stays tenant-free: migration 0002 creates the initial pages
(`pages.0004_tenant` backfills them to the default tenant), while the
UI test base and new tenants get their copies through
`pages.services.seed_tenant_pages` — loaddata cannot resolve the
tenant (fixture-pinned pks drift once the test-runner flush re-seeds
tenants).

## See also

- [Core](/apps/core.md) — `OnlyAdminMixin`, modal confirm, context processors
- [Tenants](/apps/tenants.md) — TenantModel scoping, per-tenant seeding
- [Dev setup](/setup-dev.md) — fixture loading in a dev environment
