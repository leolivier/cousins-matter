---
type: Feature Spec
title: Media Storage
description: Design of the storage layer — the two media roots and their URL prefixes, the STORAGES alias switch driven by MEDIA_STORAGE, the pluggable backend contract, and the Dropbox option
tags: ["spec", "media"]
status: draft
stale_after: 2027-11-26
generated: { by: claude-code/glm-5.3-flash, at: 2026-11-27T00:00:00Z }
---

# Media Storage

Media is deliberately served **through Django, never by the web server**: the
URL prefixes are Django routes, so the default storage backend can be swapped
for a remote one (S3, Dropbox, …) without changing a single URL or view. The
mechanics of the two prefixes and the download views are in
[Protected Media](/modules/protected-media.md); operator setup recipes are in
user-manual/media-storage.md and user-manual/media-storage-with-dropbox.md.
This fiche is the contract and the invariants.

## The two roots, one backend switch (config/settings/base.py)

- `MEDIA_ROOT = BASE_DIR/media`, `MEDIA_URL = "/protected_media/"` —
  everything members upload; login required.
- `PUBLIC_MEDIA_ROOT = MEDIA_ROOT/"public"`, `PUBLIC_MEDIA_URL =
  "/public_media/"` — the anonymous subset (site logo, theme stylesheet).

`STORAGES` has one media alias, `"default"`:

- **`MEDIA_STORAGE` unset (default):** `"default"` is a FileSystemStorage
  on `MEDIA_ROOT` / `MEDIA_URL`.
- **`MEDIA_STORAGE` set:** `"default"` becomes the remote backend given by
  `MEDIA_STORAGE` / `MEDIA_STORAGE_OPTIONS` (regression test:
  core/tests/test_media_storage_settings.py, issue #465).

The "public" subset is not a separate alias: it is the `public/` directory
prefix inside the same backend, read through `default_storage`
(`download_public_media` re-prefixes `Path("public")`). One alias means
moving media to S3 moves public and protected files together.

## Backend contract

Any Django storage backend works, because the two download views
(core/views/views_general.py: `_download_media`) always authorize first and then
serve with a per-user blake2b ETag (`"<request.user.username>@<media>"` — hence
304s are per-user even on shared files). How the bytes travel depends on the
backend: a local one is streamed in 64 KB chunks via `default_storage.open`; a
remote one (S3, R2, …) is answered with a `302` to `default_storage.url()` when
that URL is not itself under `MEDIA_URL` — after an `exists()` HEAD, since
signing succeeds for keys that do not exist — so the object store serves the
transfer and the application server only answers the authorization. Streamed
protected responses are `Cache-Control: private` (browser-only cache), public
ones `public`; the redirect carries a shorter `private` max-age so the browser
never caches a signed URL past its expiry. Generated thumbnails carry a
content-digest suffix so the path-derived ETag actually changes when the image
is regenerated.

The corollaries:

- a backend needs only read support for serving, but uploads go through the
  same `default_storage`, so it needs write support too; a backend that can sign
  URLs also needs no egress bandwidth on the application side;
- file *paths* are just relative names, and they are mode-dependent: with
  `MULTI_TENANT_ENABLED` off they are flat (`avatars/…`, `galleries/…`),
  with it on every protected upload is prefixed with the tenant slug
  (`<slug>/avatars/…`, `<slug>/galleries/…`) — see *Tenant folders* below;
- direct links to `MEDIA_URL` from outside bypass nothing: `/protected_media/`
  is a Django route guarded by `LoginRequiredMiddleware`, and in
  multi-tenant mode `download_protected_media` additionally requires the
  first path segment to be the caller's tenant slug (platform superusers
  stay unscoped).

## Tenant folders (multi-tenant mode only)

`tenants/storage.py` provides the path contract:

- `tenant_prefix(instance)` returns `""` when `MULTI_TENANT_ENABLED` is off
  (self-hosted mono-tenant paths are unchanged) and the tenant slug
  otherwise — the instance's tenant, else the active tenant, else the
  seeded default tenant;
- `tenant_path(instance, *parts)` joins that prefix with the relative
  path; every media `upload_to` goes through it
  (`galleries/models.py`, `classified_ads/models.py`, `members/models.py`,
  `troves/models.py`);
- `move_file(storage, old, new)` moves one file through the generic Storage
  API (shared by gallery moves and the migration command).

Resulting layout with the flag on:

```
media/<tenant-slug>/galleries/<gallery full_path>/[thumbnails/]<file>
media/<tenant-slug>/avatars/<file>            (+ avatars/mini_<file>)
media/<tenant-slug>/classified_ads/<ad id>/[thumbnails/]<file>
media/<tenant-slug>/troves/{pictures[/thumbnails],files}/<file>
```

Public site logos are deliberately **not** tenant-foldered: they live at
`public/logos/<tenant slug><ext>`, already unique and served anonymously.
`public` and the legacy media roots (`avatars`, `classified_ads`, `tmp`,
`env_check`, plus the already-reserved `galleries`, `troves`, …) are
reserved tenant slugs (`tenants/models.py`), so a family can never shadow
the public prefix or a legacy directory.

Files uploaded before the feature was enabled (or before the flag was turned
on) keep their old names until
`manage.py migrate_media_to_tenant_dirs` moves them and rewrites the DB
columns. The command is idempotent and supports `--dry-run`; it is a no-op
when `MULTI_TENANT_ENABLED` is off. Until it runs, tenant members get a 404
on their own old files (superusers still read them). Renaming a tenant slug
afterwards invalidates every stored path.

## Dropbox option

`django-storages[dropbox,s3]` is already a project dependency
(pyproject.toml), so **S3 and Dropbox need no extra install** — the Docker
`pip install django-storages[<backend>]` recipes in the user manual are only
for *other* backends (Azure, GCS, FTP, …). Enabling either is just:

```
MEDIA_STORAGE=storages.backends.dropbox.DropboxStorage
MEDIA_STORAGE_OPTIONS='{"app_key":…, "app_secret":…, "oauth2_refresh_token":…}'
```

Status caveat, worth knowing before recommending it: the user-manual page
banner currently states **only S3-based storage works and Dropbox is broken**
(attributed to a django-storages issue), even though the Dropbox recipe and
the dependency are maintained. Cloudflare R2 (S3-compatible) is the tested
non-default backend.

# See also

- [Protected Media](/modules/protected-media.md) — URL prefixes, download views, ETag
- [Multi-Tenancy](/specs/multi-tenancy.md) — tenant scoping and flags
- [Architecture](/architecture.md#static-and-media) — static files are a separate story (WhiteNoise)
- user-manual/media-storage.md, user-manual/media-storage-with-dropbox.md — setup and migration recipes
