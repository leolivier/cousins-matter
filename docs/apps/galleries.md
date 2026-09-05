---
type: App Reference
title: Galleries
description: Photo/video galleries — nested gallery tree, photo import (single and bulk zip via Django-Q), thumbnails, protected storage
tags: ["app", "galleries"]
status: draft
stale_after: 2027-03-04
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T12:00:00Z }
---

# Galleries

`galleries` manages photo (and video) galleries: a nested tree of
`Gallery` nodes holding `Photo` items, bulk import from a zip archive,
and automatic thumbnail generation. Both models inherit
[TenantModel](/apps/tenants.md) so every query is tenant-scoped through
`TenantManager`. Entry in the navbar is gated by the `show_galleries`
[feature flag](/apps/core.md#feature-flags-and-context-processors).

## Models (galleries/models.py)

### Gallery

- `name`, `description`, `slug` (slugified from name on `clean()`),
  `owner` (FK `members.Member`), `cover` (FK `Photo`, `SET_NULL`).
- `parent` FK to `self` builds the tree; a gallery cannot be its own
  parent, and slugs are unique per `(tenant, slug, parent)` —
  duplicated slug under a different parent is allowed and produces a
  friendly `ValidationError` otherwise.
- `full_path()` joins the ancestors' slugs (`<parent path>/<slug>`);
  it is the **storage path** of the gallery (see below).
- `rec_children_list()` collects the subtree's gallery ids with a BFS
  in Python (one query + in-memory children map, no recursive SQL).
- `cover_url()` returns the protected URL of the cover's thumbnail, or
  `settings.DEFAULT_GALLERY_COVER_URL` when no cover.

### Photo

- `image` `FileField` (photos **and** videos, `is_video_file()` from
  `core.utils` decides), `thumbnail` `ImageField`, `name`, `slug`,
  `description`, `date`, `gallery` FK (`CASCADE`),
  `uploaded_by` FK `Member`.
- Upload paths (`photo_path`/`thumbnail_path`): under
  `MEDIA_ROOT/settings.GALLERIES_DIR` (`"galleries"`,
  config/settings/base.py) **inside the gallery's `full_path()`**,
  thumbnails in a `thumbnails/` subfolder. Renaming a photo or moving
  it to another gallery rewrites the file on storage to match the new
  path.
- Constraints/indexes: slugs unique per `(tenant, slug, gallery)`;
  indexes on `(tenant, gallery)`, `(tenant, name)`,
  `(tenant, gallery, id)`.
- `save()` runs `ensure_tenant()` + `full_clean()`, then wraps
  photo + thumbnail creation in `transaction.atomic()` so a thumbnail
  failure never leaves a photo without its thumbnail
  (issue #120). Videos get `create_video_thumbnail`, images
  `create_thumbnail` — both from [core.utils](/apps/core.md), sized by
  `settings.GALLERIES_THUMBNAIL_SIZE` (300 px).
- Files are deleted through a `post_delete` receiver wrapped in
  `transaction.on_commit()` so cascading gallery deletes only remove
  files once the rows are really gone.

`galleries/validators.py` adds `validate_zipfile_extension` (`.zip`
only) for the bulk-upload form; `check_image_size` (models.py) enforces
`MAX_PHOTO_FILE_SIZE` (5 MB) or `MAX_VIDEO_FILE_SIZE` (20 MB).

## Storage is protected

Photo files never live under `/media/public/`: they sit in
`MEDIA_ROOT/galleries/...` and are streamed by the
[protected media](/modules/protected-media.md) view, which checks
login (and tenant) per request. Templates must build URLs with the
`protected_media_url` helper (`core.utils`), as `cover_url()` does.

## Views and URLs (galleries/urls.py, `app_name = "galleries"`)

- `""` — `GalleryTreeView` (tree built by `build_gallery_tree()` in
  services.py: all galleries in one query, children attached in Python
  as `cached_children`, no N+1).
- `"<slug:slug>"` (+ `/<page>`) — `GalleryDetailView` on
  `get_gallery_detail_queryset()` (owner/parent/cover selected, photo
  count annotated, children prefetched); paginated photo grid.
- `create`, `"<slug:parent_gallery>/createsub"`, `edit`, `delete`
  (`delete_gallery` uses `confirm_delete_modal` from core.utils).
- `photo/<pk>` — `PhotoDetailView`, `edit_photo`, `delete_photo`,
  `get_fullscreen_photo` (prev/next navigation via
  `get_next_prev_photo()` in services.py).
- `<slug:gallery>/photos` — `PhotoAddView` (single upload).

## Bulk zip import

`BulkUploadPhotosView` (`galleries/views/views_bulk.py`,
`bulk_upload`) accepts a zip file and hands it to `handle_zip()`
(`galleries/services.py`):

1. The zip is extracted to a temp directory; `ZipImport` (a dataclass
   in `galleries/tasks.py`) is created and registered in the in-memory
   `ZIP_IMPORTS` dict keyed by a `task_group` uuid.
2. Directory tree → gallery tree: `_get_or_create_gallery()` creates
   missing galleries recursively inside one `transaction.atomic()`
   (paths are normalized and checked for `..`, raising
   `SuspiciousFileOperation` on traversal attempts; existing galleries
   are reused untouched so hand-written descriptions survive).
   Folders without images are skipped; only their ancestor galleries
   that contain images get created, via `_get_parent_gallery()` on
   the image-bearing folders' paths.
3. One Django-Q task per image: `handle_photo_file()` →
   `create_photo()`, wrapped in `tenant_context(...)` because the
   Q worker has no request/middleware
   (see [Tenants](/apps/tenants.md)). Images are exif-transposed,
   re-encoded to JPEG (quality 90), dated from EXIF
   `DateTimeOriginal`/`DateTime`, and a photo with the same name in
   the same gallery is **overwritten**. Errors are captured and
   reported per photo instead of aborting the import.

Progress is polled by HTMX: `upload_progress/<group_id>` reads
`ZipImport.get(group)` plus Django-Q's `count_group`/`result_group`,
renders `core/common/progress-bar.html` and, when finished, cleans the
temp directory, unregisters the `ZipImport` and shows a summary
(galleries and photos created, per-photo errors).

## See also

- [Core](/apps/core.md) — protected media, thumbnails helpers, feature flags
- [Tenants](/apps/tenants.md) — tenant scoping of galleries/photos, `tenant_context` in Q workers
- [Protected media](/modules/protected-media.md) — why gallery files are never public
- [Notifications](/modules/notifications.md) — not used here (galleries do not notify followers)
- `user-manual/media-storage.md` — where media live and how they are served
