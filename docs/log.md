# Log

## 2026-11-27

- Media downloads on a remote backend (S3, Cloudflare R2, MinIO) now answer a `302` to the signed object URL instead of streaming through Django, so bytes and egress never transit the application server; filesystem deployments keep streaming. The redirect carries a shorter `private` max-age than the signed URL lifetime, and an `exists()` HEAD keeps a missing object from reaching the bucket's XML 404.

## 2026-09-05

- Root fiches: architecture, conventions, setup-dev, testing.
- App fiches (11): members, core, tenants, galleries, forum, chat, polls, classified-ads, pages, troves, genealogy.
- Module fiches (6): followers, notifications, protected-media, feature-flags, themes, management-commands.
- Flow fiches (4): member-invitation, gedcom-import-export, gallery-bulk-import, oauth-login.
- Spec fiches (3): multi-tenancy, oauth-authentication, media-storage.
- Plan fiches: plan/roadmap, plan/debt.
- Added index.md (this bundle's directory) and log.md, documented the maintenance rule in `CLAUDE.md`, and fixed six dead anchors pointing into `apps/core.md`.

## 2026-09-04

- Created the OKF bundle: root fiches (architecture, conventions, setup-dev, testing), 11 app fiches, 6 module fiches, 4 flow fiches, 3 feature specs, plan/roadmap + plan/debt, and the `manage.py check_okf` conformance check wired into `make check`.
- All fiches `status: draft`, `stale_after: 2027-03-04` (plan/ fiches: 2026-12-04).
