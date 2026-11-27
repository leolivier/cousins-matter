---
type: Module Reference
title: Protected Media
description: The two media URL prefixes (/protected_media/, /public_media/), the streaming download views, storage settings, and what makes public media public
tags: ["module", "media"]
status: draft
stale_after: 2027-11-26
generated: { by: claude-code/glm-5.3-flash, at: 2026-11-27T00:00:00Z }
---

# Protected Media

Member content (avatars, photos, attachments) lives under `media/` and is
**never** linked directly: both media prefixes are Django routes that
authorize the request, so authentication always applies. On a local filesystem
the route then streams the bytes through Python; on a remote backend it answers
a redirect to a signed object URL and the bytes never touch this server (see
below). This is the one rule to remember — build media URLs with the helpers,
not with `MEDIA_URL` string concatenation in templates.

## URL prefixes and routes

`config/settings/base.py`:

- `MEDIA_ROOT = BASE_DIR/media`, `MEDIA_URL = "/protected_media/"` —
  everything uploaded through the default storage;
- `PUBLIC_MEDIA_ROOT = MEDIA_ROOT/"public"`, `PUBLIC_MEDIA_URL =
  "/public_media/"` — the anonymous subset (theme stylesheet, site logo, ...).

Routes in cousinsmatter/urls.py (`name="get_protected_media"` and
`name="get_public_media"`, both `"<path:media>"` under the prefix above).
Helpers: `protected_media_url()` in core/utils.py and its
`{% value|protected_media_url %}` filter in core/templatetags/cm_tags.py.

## Views (core/views/views_general.py)

Both views funnel into `_download_media`:

- answers `If-None-Match` with a quoted blake2b ETag built from
  `"<request.user.username>@<media>"` (RFC 7232 quoting; cheap per-user
  caching, `304` when unchanged — answered before the storage is opened or
  signed, so a revalidation costs no remote read) and raises `Http404` on
  missing/unreadable files;
- **local backends**: streams the file in 64 KB chunks via `default_storage.open`,
  `Content-Disposition: inline`, guessed MIME type;
- **remote backends**: `_direct_media_url()` asks the backend for its own URL;
  when that URL is not served by this view (an absolute URL from S3, Cloudflare
  R2, MinIO, …) the response is a `302` to it with `Cache-Control: private,
  max-age=300` — deliberately shorter than the signed URL lifetime
  (`AWS_QUERYSTRING_EXPIRE`), or the browser would cache an expired link — so
  bandwidth and egress stay off the application server. A signed URL is issued
  for any key, so the view checks `default_storage.exists()` first (one HEAD)
  and answers its own **404** rather than sending the browser to the bucket's
  XML error page. `FileSystemStorage` answers with a path under `MEDIA_URL` —
  the URL this very view serves — so a filesystem deployment keeps streaming
  instead of looping;
- sends `Cache-Control: private, max-age=3600` on a streamed response: the
  browser caches, but shared caches (CDN, corporate proxies) must not, because
  the cache key cannot carry the user identity outside an Enterprise CDN.
  `/public_media/` sends `public, max-age=86400` instead — it is anonymous and
  identical for every visitor, so a CDN may serve it;
- the ETag is derived from the path, so regenerated thumbnails get a
  content-digest suffix (`<stem>-<8 hex>.webp`, `core.utils.versioned_thumbnail_name`)
  and therefore a new URL — otherwise clients would keep the stale copy. When
  putting a CDN in front of the app, keep `/protected_media/*` out of its cache
  (Cloudflare: a *Bypass cache* rule) or private media leaks between users;
- `download_protected_media` requires a login: it is a normal view and
  `core.middleware.LoginRequiredMiddleware` forces authentication on every
  path not listed in `LOGIN_REQUIRED_IGNORE_PATHS`
  (config/settings/base.py) — media prefixes are deliberately *not* exempted;
- in multi-tenant mode (`MULTI_TENANT_ENABLED`) the same view also checks
  that the path's first segment is `request.tenant.slug` and answers
  **404** otherwise. Platform superusers have `request.tenant = None` and
  stay unscoped (useful to inspect another family's files, and to verify a
  migration); with the flag off the check is skipped entirely because
  mono-tenant paths have no tenant segment;
- `download_public_media` is decorated `@login_not_required` and serves
  `PUBLIC_MEDIA_ROOT` only — the path it receives is re-prefixed with
  `public/` under `MEDIA_ROOT`, so nothing outside `media/public/` can leak
  through it.

Protected uploads are tenant-foldered in multi-tenant mode
(`media/<tenant slug>/…`); see [Media Storage](/specs/media-storage.md) for
the layout and `manage.py migrate_media_to_tenant_dirs` for migrating files
uploaded before the change.

## Storage settings

`STORAGES` (config/settings/base.py) defines one media storage, `"default"`
(rooted at `MEDIA_ROOT`, base_url `MEDIA_URL`). Setting `MEDIA_STORAGE`
(plus `MEDIA_STORAGE_OPTIONS`) replaces that alias with any Django storage
backend, e.g. S3; the download views go through `default_storage`, so they
follow. The "public" subset is the `public/` prefix inside the same backend.
Static files are separate (WhiteNoise) —
[Architecture](/architecture.md#static-and-media).

Contrast: files under `media/public/` are world-readable (no login) by
design; anything else needs an authenticated session. When you upload
something that must be reachable from unauthenticated contexts (email
images, the theme stylesheet, the site logo), put it in the public storage —
see core/tests/test_site_logo.py for the pattern.

# See also

- [Core](/apps/core.md#protected-media) — same views, core-app context.
- [Themes & Customization](/modules/themes.md) — `theme.css` is public media.
- [Architecture](/architecture.md#static-and-media) — proxies and static
  assets.
- User manual: media storage at
  <https://cousins-matter.readthedocs.io/media-storage/>.
