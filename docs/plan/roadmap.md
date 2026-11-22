---
type: Plan
title: Roadmap
description: In-flight and planned work — open GitHub issues, multi-tenancy follow-ups from PR #457, and the OKF documentation effort (reviewed 2026-11-22)
tags: ["plan"]
status: draft
stale_after: 2027-02-22
generated: { by: claude-code/glm-5.3-flash, at: 2026-11-22T12:22:29Z }
---

# Roadmap

Snapshot of in-flight and planned work, taken **2026-09-05** from three
sources: the open GitHub issues (at the time: 6, all `enhancement`),
`release.txt` (v0.9.2), and `git log --oneline -30`. Plans rot: re-run
`gh issue list --limit 30 --state open` and `git log --oneline -30`
before acting on anything below. Known shortcuts live in
[Known Debt](/plan/debt.md), not here.

## Shipped recently

- **v0.9.2** (`release.txt`) — the release marker the docs bundle is
  written against.
- **Multi-tenancy** (PR #457): shared-schema isolation via
  [TenantModel](/apps/tenants.md#scoping-primitives-tenantsscopingpy)
  and `TenantMiddleware`, per-family feature-flag overrides
  ([feature flags](/modules/feature-flags.md)), and RLS hardening
  ([tenants/rls.py](/apps/tenants.md#rls-hardening-tenantsrlspy),
  [spec](/specs/multi-tenancy.md)). Follow-ups below.
- **#462** — multi-write flows wrapped in `transaction.atomic` with
  file/DB ordering fixed (e.g. photo save + thumbnail).
- Dependency and CI housekeeping: django-q2 pin (#461), reusable
  test-install CI (#459/#460).

## In flight

- **OKF documentation bundle** (this `docs/` tree): root, app, module,
  flow and spec fiches plus the `make check-docs` conformance check
  (`core/management/commands/check_okf.py`). Remaining: `index.md`,
  `log.md`, this `plan/` pair, and the maintenance workflow.

## Planned — open GitHub issues

All six open issues are enhancements; the order below is by number
(newest first), not priority.

- **#458** — replace pagination (members, galleries, …) with infinite
  scroll. Touches every list view's page-size settings (e.g.
  `DEFAULT_GALLERY_PAGE_SIZE`, `DEFAULT_TROVE_PAGE_SIZE`).
- **#412** — Let's Encrypt in nginx (deployment/Docker concern, see
  [architecture](/architecture.md#docker-topology)).
- **#153** — address sanitization
  ([members](/apps/members.md) addresses).
- **#146** — keyboard shortcuts (`good first issue`).
- **#140** — environment checker surfaced to admins.
- **#43** — humanize screens (overall UX pass).

## Multi-tenancy follow-ups (from #457)

Deliberately left open when the tenant foundation landed; tracked as
debt items in [Known Debt](/plan/debt.md) with code anchors:

1. **Tenant-scope the remaining apps** —
   [forum](/apps/forum.md), [polls](/apps/polls.md),
   [classified ads](/apps/classified-ads.md), [pages](/apps/pages.md),
   [troves](/apps/troves.md), [genealogy](/apps/genealogy.md)
   ([what is not tenant-scoped](/specs/multi-tenancy.md#what-is-not-tenant-scoped)).
   Converting an app means extending `TENANT_RLS_TABLES`
   (tenants/rls.py:21) in the same change.
2. **Cross-worker flag invalidation** — tenant *settings* are versioned
   through the shared cache, but the per-tenant *flags* memo is still per
   process. Accepted while daphne is the only web process (qcluster never
   renders templates); revisit if a second web worker is added. See
   [feature flags](/modules/feature-flags.md) and
   [debt](/plan/debt.md#feature-flags-are-still-memoized-per-process).

## See also

- [Known Debt](/plan/debt.md) — the shortcut side of this list
- [Multi-tenancy spec](/specs/multi-tenancy.md) — isolation invariants
  the follow-ups must respect
- [Architecture](/architecture.md) — module map for the touched areas
