---
type: App Reference
title: Troves
description: Troves app (`troves`) — the family's numeric treasures (texts, photos, music, videos…) filed by category, with ownership-based editing and auto-generated thumbnails; documented in apps/troves.md
tags: ["app", "troves"]
status: draft
stale_after: 2027-09-13
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T22:53:05Z }
---

# Troves

`troves` is the family's attic: a flat list of "treasures" — a required
photo, a rich-text description, and an optional attached file (a scanned
text, a music recording, a video…) — grouped in six fixed categories
(`CATEGORY_CHOICES` in troves/models.py): history & stories, recipes,
cousinades (family meetings), recollections, arts, miscellaneous.

**Tenant note:** `Trove` inherits
[TenantModel](/apps/tenants.md) — tenant-scoped (`tenant` FK +
`TenantManager`, RLS backstop via `tenants.0005_rls_troves`; conversion
migration `troves.0005_tenant` backfilled legacy rows to the default
tenant). Treasures are invisible cross-tenant.

## Model (troves/models.py)

- `Trove` — `title` (110 chars, shown in the list), `description`
  (rich text, shown in the details), `picture` (required,
  `settings.TROVE_PICTURE_DIRECTORY`), `thumbnail` (generated, never
  user-facing input), `file` (optional attachment,
  `settings.TROVE_FILES_DIRECTORY`), `url` (optional external URL of
  the treasure, e.g. a YouTube video; see below), `category` (indexed),
  `owner` FK `AUTH_USER_MODEL` (`Member`).
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
- Field labels are translatable: `title` / `description` verbose names
  use `gettext_lazy`, in `models.py` as well as in historical migrations
  0003/0004, so `makemessages` extracts them; the five catalogs live in
  `troves/locale/<lang>/LC_MESSAGES/` (`.mo` files are Git LFS).
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
  `TROVE_PICTURE_FILE_MAX_SIZE` are defined but **not enforced by any
  upload path today** — troves has no equivalent of the galleries
  `check_file_size` (core/utils.py); define them in `.env`, but expect
  no server-side rejection;
- `TROVE_DESCRIPTION_MAX_SIZE` reuses `MESSAGE_MAX_SIZE` and is the
  only one wired up, as the Summernote `maxsize`
  (troves/templates/troves/treasure_form.html).

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

## External URL treasures

A treasure may point at an external resource instead of (or in addition
to) a file: `Trove.url` is an optional `URLField`. On the detail page:

- a **YouTube** URL (watch / youtu.be / shorts forms, matched by
  `_YOUTUBE_ID_RE` in troves/models.py) is embedded through the
  `embed_url` property, which rebuilds a
  `https://www.youtube-nocookie.com/embed/<id>` URL server-side;
- **any other https URL is embedded as-is** (the iframe is served
  cross-origin, so the embedded page can never reach the site's DOM);
  `http://` URLs and exotic schemes are rendered as a plain external
  link instead (mixed content is blocked on https pages anyway);
- the enforced CSP allows iframes from any https origin
  (`frame-src: https:` in config/settings/base.py) — `frame-ancestors:
  'none'` still prevents the family site from being framed elsewhere.

## Rich-text sanitization (stored XSS fix)

`description` and `title` were historically rendered with
`{% autoescape off %}` with no server-side cleaning: any member could
store `<script>` or `onerror=` handlers (stored XSS). Treasures now:

- render `description` through the `sanitize` template filter —
  `sanitize_rich_html` (core/utils.py) on top of **nh3**, an allowlist
  cleaner (summernote-style tags + `href/src/alt/class` attributes,
  `http/https/mailto` URL schemes only, `rel="noopener noreferrer"`
  forced on links). Because the filter runs at render time, data stored
  before the fix is cleaned too;
- render `title` with Django's default autoescaping (it is plain text,
  not rich text).

The same pattern is now shared: [forum](/apps/forum.md) and
[galleries](/apps/galleries.md) rich-text fields use the `sanitize`
filter too, and polls / framework messages / e-mails rely on default
escaping — see [core](/apps/core.md).

## Tests

`troves/tests/tests.py` — model CRUD and list/create/update flows, plus
`TestTroveDetailSecurityAndUrl` (script/onerror stripped from the
rendered description, title XSS payload escaped in the list, YouTube
watch/youtu.be/shorts URLs embedded via youtube-nocookie, non-YouTube
URL rendered as a link). Response
assertions search for the escaped category label
(`escape(Trove.translate_category(...))`): the template renders it under
Django's autoescape, so searching the raw label only passes when the active
translation contains no `&` (fr) — it broke once tests were pinned to `en`.

## See also

- [Core](/apps/core.md) — `Paginator`, `RichTextarea`, thumbnail helper
- [Galleries](/apps/galleries.md) — where the thumbnail pipeline comes from
- [Tenants](/apps/tenants.md) — why troves is not tenant-scoped (yet)
