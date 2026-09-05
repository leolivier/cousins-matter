---
type: Module Reference
title: Protected Media
description: The two media URL prefixes (/protected_media/, /public_media/), the streaming download views, storage settings, and what makes public media public
tags: ["module", "media"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T11:16:06Z }
---

# Protected Media

Member content (avatars, photos, attachments) lives under `media/` and is
**never** served directly by the web server: both media prefixes are Django
routes that stream files through Python, so authentication applies. This is
the one rule to remember — build media URLs with the helpers, not with
`MEDIA_URL` string concatenation in templates.

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

- streams the file in 64 KB chunks via `default_storage.open` (works with any
  storage backend, e.g. S3), `Content-Disposition: inline`, guessed MIME type;
- answers `If-None-Match` with a blake2b ETag built from
  `"<request.user.username>@<media>"` (cheap per-user caching, `304` when
  unchanged) and raises `Http404` on missing/unreadable files;
- `download_protected_media` requires a login: it is a normal view and
  `core.middleware.LoginRequiredMiddleware` forces authentication on every
  path not listed in `LOGIN_REQUIRED_IGNORE_PATHS`
  (config/settings/base.py) — media prefixes are deliberately *not* exempted;
- `download_public_media` is decorated `@login_not_required` and serves
  `PUBLIC_MEDIA_ROOT` only — the path it receives is re-prefixed with
  `public/` under `MEDIA_ROOT`, so nothing outside `media/public/` can leak
  through it.

## Storage settings

`STORAGES` (config/settings/base.py) defines two file storages: `"default"`
(rooted at `MEDIA_ROOT`, base_url `MEDIA_URL`) and `"public"` (rooted at
`PUBLIC_MEDIA_ROOT`). Setting `MEDIA_STORAGE` (plus `MEDIA_STORAGE_OPTIONS`)
reconfigures **only the `public` alias** to any Django storage backend, e.g.
S3; `default` is deliberately left untouched (still FileSystemStorage on
`MEDIA_ROOT`), which is why the download views keep working — they go
through `default_storage`.
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
