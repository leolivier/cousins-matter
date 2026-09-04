---
type: App Reference
title: Classified Ads
description: Classified ads app (`classified_ads`, documented as apps/classified-ads.md) — member-to-member sale listings with photos and owner contact by email
tags: ["app", "classified_ads"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T00:00:00Z }
---

# Classified Ads

`classified_ads` lets members post sale listings (the Django app label
keeps the underscore: `classified_ads`; this fiche file uses a hyphen).
A member creates an ad with category, price and photos; other members
browse it and contact the **owner by email through a relay** — the
owner's address is never exposed. Navbar visibility is gated by the
`show_classified_ads` [feature flag](/apps/core.md#feature-flags).

**Tenant note:** `ClassifiedAd` and `AdPhoto` inherit `models.Model`
directly — **not** [TenantModel](/apps/tenants.md)-scoped (same as
[forum](/apps/forum.md) and [polls](/apps/polls.md)).

## Models (classified_ads/models.py)

- `ClassifiedAd` — `title`, `category`/`subcategory` (free-form char
  fields validated against the catalogue, see below), `description`,
  `price` (CharField — free text, e.g. "50 €" or "free"),
  `shipping_method` (`pickup`/`shipping`/`both`), optional `location`,
  `item_status` (new → parts), `ad_status`
  (`for_sale`/`sold`/`closed`), `owner` FK `Member`. Indexed on
  (`owner`, `category`, `subcategory`), ordered by `-date_created`.
- `AdPhoto` — `image` + generated `thumbnail`
  (`create_thumbnail`, size `GALLERIES_THUMBNAIL_SIZE`), FK `ad`
  (`related_name="photos"`). Files land under
  `MEDIA_ROOT/classified_ads/<ad id>/` via `get_photo_path`.
  `save()` wraps row + thumbnail in `transaction.atomic()` and, if
  thumbnail generation fails on a new photo, deletes the orphaned
  image from storage (issue #120); `delete()` removes the files only
  after the row deletion succeeded.
- `Categories` — a static helper over the catalogue dict in
  classified_ads/categories.py (translated labels + subcategories).
  It backs the ad form and the `display_category`/
  `display_subcategory` helpers, plus the HTMX
  `subcategories` endpoint that re-renders the subcategory select
  when a category is picked.

## Publication and moderation rules

There is **no pre-publication moderation**: an ad is visible in the
list as soon as it is created. The effective publication rules are:

- `ListAdsView` shows only `ad_status="for_sale"` ads, newest first.
- Life-cycle transitions (`sold`, `closed`) are **Django-admin only** —
  no member-facing view changes `ad_status`; admins manage it from the
  admin list (filterable by status/category/date).
- Contact is mediated: `send_message`
  (classified_ads/urls.py `<pk>/send-message`) renders a form and
  `do_send_ad_message` (classified_ads/services.py) emails the owner
  with the sender's name/address in the body, `fail_silently=False`
  — an SMTP failure raises rather than pretending success.
- Creation is open to any member (`form.instance.owner =
  request.user`); edit, delete, photo add/delete go through
  `core.utils.check_edit_permission` (owner or staff).

## Views and URLs (classified_ads/urls.py, `app_name = "classified_ads"`)

- `""` — `ListAdsView` (for-sale ads, `select_related("owner")`).
- `create`, `<pk>/update`, `<pk>/delete` (confirm modal) — the CRUD
  surface; delete answers HTMX with a redirect to the list.
- `<pk>/detail` — `AdDetailView`, `select_related("owner")`
  + `prefetch_related("photos")`.
- Photos: `<pk>/photo` (add, HTMX re-renders the gallery partial),
  `photo/<pk>/delete` (confirm modal), and
  `photo/<pk>/fullscreen` — a prev/next swipe viewer reusing the
  [galleries](/apps/galleries.md) fullscreen partial, with
  `get_next_prev_photo` (classified_ads/services.py) resolving the
  neighbour photo or raising `AdPhoto.DoesNotExist`.

## Known performance issue

N+1 query findings on the list/detail rendering paths are tracked in
[/plan/debt.md](/plan/debt.md) (full analysis captured at
`classified_ads_n+1_analysis.md` in the repo root); do not restate it
here.

## See also

- [Core](/apps/core.md) — `check_edit_permission`, modal confirm, feature flags
- [Galleries](/apps/galleries.md) — thumbnail helper and fullscreen viewer
- [Tenants](/apps/tenants.md) — scoping model this app does not use yet
