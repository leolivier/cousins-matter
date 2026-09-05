---
type: Feature Spec
title: Media Storage
description: Design of the storage layer — the two media roots and their URL prefixes, the STORAGES alias switch driven by MEDIA_STORAGE, the pluggable backend contract, and the Dropbox option
tags: ["spec", "media"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T12:02:12Z }
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

`STORAGES` is built conditionally:

- **`MEDIA_STORAGE` unset (default):** two FileSystemStorage aliases —
  `"default"` on `MEDIA_ROOT` and `"public"` on `PUBLIC_MEDIA_ROOT`.
- **`MEDIA_STORAGE` set:** the `"default"` alias becomes
  `{"BACKEND": env.str("MEDIA_STORAGE"),
  "OPTIONS": env.json("MEDIA_STORAGE_OPTIONS", default={})}`
  and **the `"public"` alias disappears entirely** — public files become
  objects under the `public/` prefix *inside the remote backend*.

Nothing in the codebase currently selects `storage="public"`; public files
are simply files under `media/public/` reached through `default_storage`
(`download_public_media` re-prefixes `Path("public")`). So the whole public
mechanism is a directory convention, not a storage routing decision — keep it
that way unless both aliases are migrated together.

## Backend contract

Any Django storage backend works, because the two download views
(core/views/views_general.py: `_download_media`) only ever call
`default_storage.open` and stream in 64 KB chunks with a per-user blake2b ETag
(`"<request.user.username>@<media>"` — hence 304s are per-user even on shared
files). The corollaries:

- a backend needs only read support for serving, but uploads go through the
  same `default_storage`, so it needs write support too;
- file *paths* are just relative names (`avatars/…`, gallery paths) — there is
  no tenant component in them, so [Multi-Tenancy](/specs/multi-tenancy.md)
  isolation for media is enforced at the view/DB layer, never by storage
  layout;
- direct links to `MEDIA_URL` from outside bypass nothing: `/protected_media/`
  is a Django route guarded by `LoginRequiredMiddleware`, which is the actual
  security boundary.

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
- [Multi-Tenancy](/specs/multi-tenancy.md) — why media paths carry no tenant
- [Architecture](/architecture.md#static-and-media) — static files are a separate story (WhiteNoise)
- user-manual/media-storage.md, user-manual/media-storage-with-dropbox.md — setup and migration recipes
