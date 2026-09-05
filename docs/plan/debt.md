---
type: Plan
title: Known Debt
description: Known shortcuts, latent bugs and unenforced settings, each anchored to the code that carries them (verified 2026-09-05)
tags: ["plan", "debt"]
status: draft
stale_after: 2026-12-04
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T12:28:11Z }
---

# Known Debt

Deliberate shortcuts and latent defects, each anchored to a file so the
next reader can re-verify it in seconds. Planned work derived from these
items lives in the [Roadmap](/plan/roadmap.md). Facts below were checked
against the code on 2026-09-05.

## Gallery bulk import: invalid-form branch raises TypeError

`galleries/views/views_bulk.py:56` flashes form errors with
`": ".join(code, error)` — `str.join` takes one argument, so any
**invalid** bulk-import form raises `TypeError` and the user gets an
HTTP 500 instead of the field errors. (`form.errors.items()` also yields
a list of messages as `error`, so the fix is formatting, e.g.
`f"{code}: {'; '.join(error)}"`.) The sibling `except Exception` branch
just above flashes raw `str(e)`. User-visible failure modes are listed
in the [gallery bulk import flow](/flows/gallery-bulk-import.md#failure-modes-visible-to-the-user).

## Zip import progress is per-process state

`ZIP_IMPORTS` is a module-level dict (galleries/tasks.py:52) holding
in-flight `ZipImport` objects; `upload_progress` raises `Http404` when
the group is absent (galleries/views/views_bulk.py:65-67). With more
than one app-server worker — or after a worker restart mid-upload — the
progress poll hits a process that never saw the import and 404s. See
[bulk zip import](/apps/galleries.md#bulk-zip-import).

## Chat tables have no RLS policies

`ChatRoom` and `ChatMessage` are `TenantModel`-scoped
(chat/models.py:27,114), but `TENANT_RLS_TABLES`
(tenants/rls.py:21) still lists only `members_member` and the two
`galleries_*` tables, so the chat tables get **no row-level-security
backstop**. The comment at tenants/rls.py:19-20 ("Extend this list when
converting an app to TenantModel (chat, forum, polls, …)") is stale —
chat is already converted. The [RLS spec](/specs/multi-tenancy.md#rls-enforcement-points-invariants)
states the invariant this violates.

## Six apps are not tenant-scoped

[forum](/apps/forum.md) (`Message`/`Post`/`Comment`),
[polls](/apps/polls.md), [classified ads](/apps/classified-ads.md)
(`ClassifiedAd`/`AdPhoto`), [pages](/apps/pages.md)
(`FlatPage` extends `django.contrib.flatpages`),
[troves](/apps/troves.md) and [genealogy](/apps/genealogy.md)
(`Person`/`Family`) all inherit `models.Model` directly — their data is
shared across tenants (see the
[multi-tenancy spec](/specs/multi-tenancy.md#what-is-not-tenant-scoped)).
Scoping them is roadmap work; each conversion must also add its tables
to `TENANT_RLS_TABLES`.

## The `public` storage alias disappears when `MEDIA_STORAGE` is set

`STORAGES` (config/settings/base.py:131-152) defines a `public` alias
pointing at `PUBLIC_MEDIA_ROOT` **only while `MEDIA_STORAGE` is unset**;
setting `MEDIA_STORAGE` replaces that entry wholesale. Nothing selects
`storage="public"` today, so nothing breaks — but the alias is the hook
[public media](/architecture.md#static-and-media) relies on, and it
silently vanishes exactly when someone moves media to S3. See the
[media-storage spec](/specs/media-storage.md).

Suspected misplaced-key bug on top: `MEDIA_STORAGE` reconfigures `public`
where an operator would expect `default` — see the remote media storage
item in the [roadmap](/plan/roadmap.md).

## Trove size limits are unenforced

`TROVE_FILE_MAX_SIZE` (20 MB) and `TROVE_PICTURE_FILE_MAX_SIZE`
(config/settings/base.py:520-521) are read by no upload path — a grep
shows their only consumer is the settings file itself.
`TROVE_DESCRIPTION_MAX_SIZE` is enforced client-side only, via the
summernote `maxsize` include in
troves/templates/troves/treasure_form.html:4. Server-side trove uploads
are therefore unbounded by these settings.

## Per-tenant flags cache invalidation

`clear_flags_cache()` has a single caller (the family-settings save) and
`_tenant_flags_cache` is a per-process dict, so other workers serve
stale flags. The [feature-flags module fiche](/modules/feature-flags.md)
owns this analysis — do not fix it in a second place.

## Classified ads N+1 analysis (resolved in code)

`classified_ads_n+1_analysis.md` (repo root, kept on purpose) found two
N+1 query paths. Both fixes **are already in the code**:
`ListAdsView` uses `select_related("owner")` and `AdDetailView` adds
`prefetch_related("photos")` (classified_ads/views.py:75-90), and both
admins carry `list_select_related` (classified_ads/admin.py). The file
stays as the historical analysis; the user-facing summary is in
[apps/classified-ads.md](/apps/classified-ads.md#known-performance-issue).
Remaining cleanup: archive or delete the root file once nothing links
to it.

## Markers left in code

- **`ponytail:` marker** — galleries/models.py:156: files copied during
  a gallery move are not cleaned up on failure (rare, harmless orphans).
- **TODO/FIXME hotspots** — 15 occurrences across 13 `.py` files
  (`grep -rn "TODO\|FIXME" --include=*.py`). The heavy ones:
  - members/views/views_family.py:48 and members/views/views_address.py:45
    — "very inefficient! refactor to add a search field" (family/address
    listing scans).
  - galleries/views/views_gallery.py:68 — "every member can edit any
    gallery ???" — an open permission-design question on gallery edit.
  - core/templatetags/cm_tags.py:3 and core/htmlvalidator.py:32 —
    extract as reusable packages.
  - config/settings/production.py:33 — `SECURE_HSTS_SECONDS` still a TODO.
  - galleries/tasks.py:80 (exif as JSON), members/trace_login.py:101
    (post_migrate signal ordering), galleries/tests/tests_bulk_upload.py:88
    (test cleanup), core/views/views_general.py:145 (Windows paths), and
    3 in forum/tests (JS/HTMX interactions untestable server-side).

## See also

- [Roadmap](/plan/roadmap.md) — the work items behind these items
- [Multi-tenancy spec](/specs/multi-tenancy.md) — isolation invariants
- [Conventions](/conventions.md) — where services, flags and async
  patterns that own these fixes live
