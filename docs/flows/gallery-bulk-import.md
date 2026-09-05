---
type: Flow
title: Gallery Bulk Import
description: End-to-end zip import — extraction to galleries, per-photo Django-Q tasks, HTMX progress bar, and what happens on failure
tags: ["flow", "galleries"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T11:39:00Z }
---

# Gallery Bulk Import

A zip of photo folders becomes a tree of galleries with photos. The upload
request only *schedules* work; the photos are actually created by Django-Q2
tasks, and the user watches an HTMX progress bar. The Gallery/Photo model and
single-photo upload are covered in [Galleries](/apps/galleries.md).

## Steps

1. **Entry point.** `GET /galleries/bulk_upload` (galleries/urls.py,
   `name="bulk_upload"`) renders `galleries/bulk_upload.html` with
   `galleries/forms.py: BulkUploadPhotosForm`: a `zipfile` file field
   (`validate_zipfile_extension` + `check_zip_size` against
   `settings.MAX_GALLERY_BULK_UPLOAD_SIZE`) and an optional `gallery`
   (parent gallery `ModelChoiceField`). Login required via
   `core/middleware.py: LoginRequiredMiddleware`.
2. **Submit.** `POST /galleries/bulk_upload` →
   `galleries/views/views_bulk.py: BulkUploadPhotosView.post`. On form
   validation errors it flashes the errors and returns
   `HttpResponseClientRefresh` (HTMX re-render of the page).
3. **Scheduling.** A fresh `task_group = uuid4().hex` is generated and
   `galleries/services.py: handle_zip(zip_file, task_group, owner_id,
   root_gallery, tenant_id)` runs synchronously:
   - `zipfile.is_zipfile` check — a bad archive raises
     `BadZipFile`, caught by the view and flashed.
   - The zip is extracted to a `tempfile.mkdtemp()` temp dir; a
     `galleries/tasks.py: ZipImport` state object (temp root, counters,
     gallery cache) is registered in the in-process `ZIP_IMPORTS` dict keyed
     by the task group.
   - `os.walk` over the extraction: directories containing **no image file**
     (by `mimetypes.guess_type`) are skipped entirely; each other directory
     maps to a gallery via `galleries/services.py: _get_or_create_gallery`,
     which recursively creates missing ancestor galleries in one
     `transaction.atomic()` block and refuses path traversal (`..` →
     `SuspiciousFileOperation`). A root-level folder (`.`) requires the
     optional parent gallery to have been selected, else
     `ValidationError("Root gallery not found...")`.
   - One Django-Q `async_task(handle_photo_file, ..., group=task_group,
     hook=post_create_photo)` per image, and `nbPhotos` incremented.
   **Side effects so far:** Gallery rows (owner = importer), temp dir on
   disk, queued Q tasks.
4. **Progress bar.** The view immediately renders
   `core/common/progress-bar.html` (value 0, max = `nbPhotos`) with an
   `hx-get` polling `/galleries/upload_progress/<task_group>` every second →
   `galleries/views/views_bulk.py: upload_progress`. That view reads the
   `ZipImport` from memory (unknown/expired id → `Http404 "Upload not
   found"`), and uses `django_q.tasks.count_group` / `result_group` to show
   progress, accumulated photo paths and per-photo error strings.
5. **Per-photo tasks.** `galleries/tasks.py: handle_photo_file` activates
   the importer's tenant (`tenants/scoping.py: tenant_context`, because Q
   workers run without request/middleware) and calls `create_photo`:
   the image is opened with PIL, `exif_transpose`d, re-encoded to JPEG
   quality 90 into a buffer, its date taken from EXIF tag 36867 (fallback
   306, fallback today), then a `Photo` row is created — **or overwritten if
   a photo with the same name already exists in the same gallery**
   (documented overwrite, description "Imported from zipfile directory
   …"). Errors (OSError, `ValidationError`, anything else) are converted
   into an error string returned by the task; the task group continues with
   the next photo. **Side effects:** Photo rows, image files in protected
   media storage.
6. **Completion.** When `value == max`, `upload_progress` adds the success
   message ("Zip file uploaded: N galleries and M photos created") and the
   back-to-galleries link, then cleans up: `shutil.rmtree` of the temp dir
   and `zimport.unregister()`. End state: galleries + photos visible in the
   tree, errors listed per photo in the progress fragment.

## Failure modes visible to the user

- Not a zip / oversized zip / wrong extension: flashed error, nothing
  imported.
- `..` inside zip paths: `SuspiciousFileOperation` flashed, import aborted
  (galleries already created in earlier iterations remain).
- Root-level photos without a selected parent gallery: "Root gallery not
  found. Please select a root gallery."
- Individual unreadable/corrupt images: skipped with an error line in the
  progress bar; the rest of the zip still imports.
- Stale/unknown progress id: 404 (e.g. server restarted — `ZIP_IMPORTS` is
  in-memory and not shared across workers).
- Dev only: without `make up4run` the Q broker is unreachable and the upload
  fails with an error (`Q_SYNC=True` avoids this by running the tasks
  synchronously).

## Related

- [Galleries app](/apps/galleries.md) — models, single upload, tree view.
- No follower notifications are emitted by this flow; the `post_create_photo`
  hook only logs (galleries/tasks.py).
- [GEDCOM flow](/flows/gedcom-import-export.md) — the synchronous
  (non-task-based) bulk import for contrast.
