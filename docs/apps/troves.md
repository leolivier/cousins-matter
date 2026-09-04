---
type: App Reference
title: Troves
description: Troves app (`troves`) — the family's numeric treasures (texts, photos, music, videos…) filed by category, with ownership-based editing and auto-generated thumbnails; documented in apps/troves.md
tags: ["app", "troves"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T22:53:05Z }
---

# Troves

`troves` is the family's attic: a flat list of "treasures" — a required
photo, a rich-text description, and an optional attached file (a scanned
text, a music recording, a video…) — grouped in six fixed categories
(`CATEGORY_CHOICES` in troves/models.py): history & stories, recipes,
cousinades (family meetings), recollections, arts, miscellaneous.

**Tenant note:** `Trove` inherits `models.Model` directly — **not**
[TenantModel](/apps/tenants.md)-scoped (no `tenant` field, no
`TenantManager`). Treasures are currently shared platform-wide across
tenants, like [forum](/apps/forum.md), [polls](/apps/polls.md),
[classified ads](/apps/classified-ads.md) and [pages](/apps/pages.md).

## Model (troves/models.py)

- `Trove` — `title` (110 chars, shown in the list), `description`
  (rich text, shown in the details), `picture` (required,
  `settings.TROVE_PICTURE_DIRECTORY`), `thumbnail` (generated, never
  user-facing input), `file` (optional attachment,
  `settings.TROVE_FILES_DIRECTORY`), `category` (indexed), `owner` FK
  `AUTH_USER_MODEL` (`Member`).
- Save-time guarantees:
  - `clean()` refuses a treasure without an owner, and `save()` calls
    `full_clean()` first;
  - the row and its thumbnail commit **together**
    (`transaction.atomic()`); if thumbnail creation fails, the row is
    rolled back and — on a brand-new treasure — the orphaned picture
    file is deleted from storage (issue #120);
  - `delete()` removes the stored picture + thumbnail only after the
    row deletion succeeded, so a failed delete never leaves a row
    pointing at deleted files.
- Thumbnails reuse the galleries machinery: `create_thumbnail`
  (core/utils.py) with `settings.TROVE_THUMBNAIL_SIZE` (defaults to the
  galleries thumbnail size).

## Storage and size limits (config/settings/base.py)

Uploads go through `default_storage`, i.e. the protected media root —
treasure files are **not** under `/public_media/` and are never served
to anonymous visitors (see [architecture](/architecture.md)):

- `TROVE_PICTURE_DIRECTORY` = `troves/pictures/`,
  `TROVE_THUMBNAIL_DIRECTORY` = `troves/pictures/thumbnails/`,
  `TROVE_FILES_DIRECTORY` = `troves/files/`;
- `TROVE_FILE_MAX_SIZE` (20 MB by default) and
  `TROVE_PICTURE_FILE_MAX_SIZE` are enforced on upload;
- `TROVE_DESCRIPTION_MAX_SIZE` reuses `MESSAGE_MAX_SIZE`.

## Publication rules

There is no publish/private flag: a treasure is visible to every
logged-in member as soon as it is saved. The only access rule is
**ownership**:

- `create_treasure` (troves/views.py) forces `owner` to the current
  user — the form does not offer an owner field;
- `update_treasure` and `delete_treasure` call
  `check_edit_permission(request, treasure.owner)`
  (core/utils.py): owner, tenant admin or superuser only — anybody
  else gets a `PermissionDenied`;
- `delete_treasure` is HTMX-only (`assert request.htmx`) and answers a
  `JsonResponse({"deleted": ...})` for the confirm modal;
- all views sit behind the global `LoginRequiredMiddleware`
  (core/middleware.py) — there is no extra role gate in the app.

## Browsing (URL namespace `troves`)

- `troves:list` / `troves:page/<int:page>` — `trove_cave`: paginated
  list grouped by category (`Paginator.get_page(..., group_by="category")`,
  `DEFAULT_TROVE_PAGE_SIZE` = 10), optional `?category=` filter whose
  pagination links preserve the filter; out-of-range pages redirect
  (`PageOutOfBounds`) instead of 404-ing.
- `troves:create`, `troves:update`, `troves:detail` — one
  `TreasureForm` (`description` rendered with the
  `RichTextarea` widget from core/widgets.py).
- The `translate_category` filter (troves/templatetags/troves_tags.py)
  displays category slugs in the current language.

## See also

- [Core](/apps/core.md) — `Paginator`, `RichTextarea`, thumbnail helper
- [Galleries](/apps/galleries.md) — where the thumbnail pipeline comes from
- [Tenants](/apps/tenants.md) — why troves is not tenant-scoped (yet)
