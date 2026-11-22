---
type: Plan
title: Known Debt
description: Remaining shortcuts and unenforced settings, each anchored to the code that carries them (verified 2026-11-22)
tags: ["plan", "debt"]
status: draft
stale_after: 2027-02-22
generated: { by: claude-code/glm-5.3-flash, at: 2026-11-22T12:22:29Z }
---

# Known Debt

Deliberate shortcuts and latent defects, each anchored to a file so the
next reader can re-verify it in seconds. Planned work derived from these
items lives in the [Roadmap](/plan/roadmap.md). Facts below were checked
against the code on 2026-11-22.

## Feature flags are still memoized per process

`_tenant_flags_cache` (core/templatetags/cm_tags.py:280) is a plain
per-process dict and `clear_flags_cache()` has a single caller, the
family-settings save (tenants/views/views_settings.py). This is accepted
today because `|featured` is only evaluated while rendering templates in
daphne (a single process; `Dockerfile:54`) — qcluster never renders
templates. Tenant **settings** are no longer affected: their memo is
versioned through the shared cache and invalidated by
`TenantSettings.save()` (tenants/settings_overrides.py).

Trigger to revisit: if a second web worker is added, give the flags memo
the same `_version()` / `cache.incr` treatment. See the
[feature-flags fiche](/modules/feature-flags.md).

## Import progress depends on the cache being up

`ZipImport` (galleries/tasks.py) and `ImportContext` (members/tasks.py)
store their progress objects in the Django cache with a 24 h TTL, so a
web restart no longer loses an in-flight import and every process sees
the same state. Production uses Redis (config/settings/production.py);
dev and tests use LocMem (single process by definition). If Redis is
down, `upload_progress` / `get_import_progress` return 404 — the import
itself still completes in qcluster, only the polling bar is lost. See
[bulk zip import](/apps/galleries.md#bulk-zip-import).

## Ownerless galleries and photos are managed by tenant admins only

`Gallery.owner` is nullable (galleries/models.py:182-188). User-created
galleries always have an owner (`GalleryCreateView.form_valid`), and
zip-imported galleries inherit the importer. Ownerless rows come from the
admin or direct ORM use; `check_edit_permission(None)` now allows only
superusers/tenant admins (core/utils.py:435), and the gallery and photo
edit paths always call it (`uploaded_by or gallery.owner` for photos).
This is a deliberate policy, not a bug — document it if a new creation
path can produce ownerless galleries.

## Trove description size is client-side only

`TROVE_FILE_MAX_SIZE` and `TROVE_PICTURE_FILE_MAX_SIZE`
(config/settings/base.py:560-561) are now enforced server-side by model
validators on `Trove.file` / `Trove.picture` (troves/models.py), through
the shared `core.utils.check_file_size`. `TROVE_DESCRIPTION_MAX_SIZE`
remains a Summernote `maxsize` hint only
(troves/templates/troves/treasure_form.html:4); its default (~2.5 MB)
makes a server-side character check pointless. See
[troves](/apps/troves.md#storage-and-size-limits-configsettingsbasepy).

## Markers left in code

- **`ponytail:` markers** — deliberate ceilings, kept on purpose:
  - galleries/models.py:156: files copied during a gallery move are not
    cleaned up on failure (rare, harmless orphans).
  - tenants/views/views_settings.py:32: site-logo limit fixed at 512 KB;
    move to an env setting only if a family needs more.
  - saas/onboarding.py:25: "invited" derives from the tenant having other
    members (no dedicated flag).
- **TODO/FIXME** — 3 occurrences, all in forum tests and all notes about
  JS/HTMX interactions that cannot be asserted server-side
  (forum/tests/tests_reply.py:48, forum/tests/tests_comments.py:42 and :54).
  Keep them as documentation.

## TokenManager stays in members

`members/registration_link_manager.py:TokenManager` has a single consumer
(`RegistrationLinkManager`); moving it to `core/` would only pay off with
a second consumer, and its `_key_salt` must stay byte-identical or every
in-flight registration link breaks. Revisit when another app needs
signed, expiring tokens.

## Recently resolved (kept for context)

- Bulk-import invalid form raised `TypeError` (`": ".join(code, error)`);
  it now flashes the field errors and logs unexpected exceptions.
- `MEDIA_STORAGE` configures the `default` alias; the phantom `public`
  alias is gone (issue #465).
- Classified ads N+1 paths use `select_related("owner")` /
  `prefetch_related("photos")`; the root analysis file was removed.
- `Tenant.name` now stands in for `site_name` in multi-tenant mode when
  no override is set (default/system tenants keep the global brand).
- `send_zipfile` (dead, never URL-wired) was deleted.

## See also

- [Roadmap](/plan/roadmap.md) — the work items behind these items
- [Multi-tenancy spec](/specs/multi-tenancy.md) — isolation invariants
- [Conventions](/conventions.md) — where services, flags and async
  patterns that own these fixes live
