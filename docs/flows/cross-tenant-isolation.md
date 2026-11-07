---
type: Flow
title: Cross-Tenant Isolation (Manual Test)
description: Manual end-to-end test scenario verifying that tenants cannot see or touch each other's data in any app — lists, direct object access, member lookups, chat, media and auth boundaries
tags: ["flow", "tenants", "testing", "manual", "isolation"]
status: draft
stale_after: 2027-04-17
generated: { by: claude-code/glm-5.3-flash, at: 2026-10-17T00:00:00Z }
---

# Cross-Tenant Isolation (Manual Test)

A manual, click-through test scenario verifying that two families (tenants)
sharing the instance never see or mutate each other's data, in every app.
It starts from the end state of
[Tenant Onboarding E2E](/flows/tenant-onboarding-e2e.md): family
`test-family-eta` with admin `nora@example.com`, member `hugo@example.com`,
inactive managed member `marta`.

**How isolation is supposed to work** (what the probes verify):
`TenantMiddleware` derives the tenant from the logged-in member and stores it
in a thread-local; every content model inherits `TenantModel`, whose
`TenantManager` filters all querysets by it (tenants/scoping.py). So a
cross-tenant access must fail as **404** (the object simply does not exist in
the scoped queryset) — never 200, never 500. Platform superusers are
deliberately **unscoped** (by design, not a leak).

## Preconditions

- Same environment as the onboarding flow: `MULTI_TENANT_ENABLED=True`,
  `make up4run` + `make run`, console emails in the terminal.
- End state of [Tenant Onboarding E2E](/flows/tenant-onboarding-e2e.md)
  present (family A `test-family-eta`, Nora/Hugo active, Marta inactive).
- A private window per session you don't want to mix (each browser profile
  keeps one tenant session at a time — logging in as someone else switches
  your tenant scope).

## Actors / test data

| ID | Who | Email | Notes |
|----|-----|-------|-------|
| A1 | Family A admin | `nora@example.com` | from the onboarding flow |
| R1 | Family A member | `hugo@example.com` | from the onboarding flow |
| I2 | Family B admin | `ira@example.com` | created in Phase 0 |
| M2 | Family B member | `lena@example.com` | created in Phase 0 |
| SU | Platform superuser | pre-existing | observations only |

## Phase 0 — Second family and marker content

1. Create family B by self-signup, exactly like onboarding Phase 1: family
   name `Isolation Family IFB`, admin `ira@example.com` → verify the email
   from the terminal, log in as Ira once. Note the slug `isolation-family-ifb`.
2. As Ira: Members → *Create member* (`lena`, email `lena@example.com`), then
   activate her manually at `/members/lena/activate/`. Log in as Lena once to
   confirm she is active.
3. Seed **marker content in every app**, once per family, with the same
   names in both families where the name is free text (deliberate slug/name
   collision):

   | App | In family A (as Hugo or Nora) | In family B (as Lena or Ira) |
   |-----|-------------------------------|------------------------------|
   | Forum (`/posts/`) | post **"ETA secret recipe"** | post **"IFB secret recipe"** — yes, same title |
   | Chat (`/chat/`) | public room **lounge** | public room **lounge** — same slug |
   | Galleries (`/galleries/`) | gallery **Reunion** with one photo | gallery **Reunion** with one photo |
   | Polls (`/polls/`) | poll "ETA picnic" | poll "IFB picnic" |
   | Genealogy (`/genealogy/`) | person "Marcus ETA" | person "Marcus IFB" |
   | Troves (`/troves/`) | trove "ETA treasury" | trove "IFB treasury" |
   | Classified ads (`/classified-ads/`) | ad "Old bike" | ad "Old bike" |
   | Pages (`/pages-edit/`) | page "ETA rules" | page "IFB rules" |

4. While seeding, **write down every pk** (visible in the URL of each detail
   page): post pk, poll pk, gallery slug + photo pk, genealogy person pk,
   trove pk, ad pk, page pk — for both families. All Phase 2+ probes use
   family B's pks, typed from family A's browser.

## Phase 1 — List scoping (positive check)

5. As Nora (family A), open each index: `/members/`, `/members/directory`,
   `/members/birthdays`, `/posts/`, `/chat/`, `/galleries/`, `/polls/all/`,
   `/genealogy/people/`, `/troves/`, `/classified-ads/`, `/pages-edit/admin`.
   **Expect**: every list shows **only** family A's items — never
   "IFB secret recipe", "Marcus IFB", Lena or Ira. The two rooms/galleries
   named identically must show only family A's instance.
6. As Lena (family B): same lists. **Expect**: mirror result — only family
   B's content, never Nora, Hugo or any "ETA" marker.

## Phase 2 — Direct object access by id (the real leak test)

7. Still as Nora (family A browser), type family B's URLs by hand, using the
   pks noted in Phase 0. **Expect 404 for every single one**:

   - `/posts/<pk_b>` (read), `/posts/<pk_b>/edit`, `/posts/<pk_b>/reply`,
     `/posts/<pk_b>/delete`, `/posts/<pk_b>/toggle-follow`
   - `/galleries/<slug_b>` (the identically-named `Reunion` must land on
     family A's gallery, not B's), `/galleries/photo/<pk_b>`,
     `/galleries/photo/<pk_b>/edit`, `/galleries/photo/<pk_b>/delete`
   - `/polls/<pk_b>/` and `/polls/<poll_b>/vote/` (no voting on their poll)
   - `/genealogy/people/<pk_b>/`, `/genealogy/people/<pk_b>/edit/`
   - `/troves/<pk_b>/detail/`, `/troves/<pk_b>/update/`, `/troves/<pk_b>/delete/`
   - `/classified-ads/<pk_b>/detail`, `/classified-ads/<pk_b>/send-message`
     (no "contact the seller" on their ad), `/classified-ads/photo/<pk_b>/fullscreen`
   - `/pages-edit/<pk_b>`

   A 403 or a redirect to home is acceptable as *deny*, but a 200 rendering
   family B's data, or a 500, is a **failure to record**.

## Phase 3 — Member lookups across tenants

8. As Nora: `/members/lena/` → **404** (scoped manager: Lena does not exist
   in family A). Same for `/members/lena/edit`, `/members/lena/delete`,
   `/members/lena/toggle-follow` (no following across families).
9. As Nora: `/members/search/?search=lena` and search for `ira` → **no
   results**. Birthdays page (`/members/birthdays`) and directory never list
   family B members (same birth dates seeded if needed to make this visible:
   give Lena the same birthday as a family A member).
10. As Hugo (plain member, not admin): `/members/create/`, `/members/import`
    → 403. `/members/marta/activate/` → denied (already covered by managed
    member rules, recall it here as an auth check).

## Phase 4 — Chat specifics

11. As Nora, open `/chat/room/lounge`. **Expect**: family A's lounge only —
    same name as family B's, but its messages and members never appear.
12. As Nora, create a private room (`/chat/private/room`): the recipient
    autocomplete proposes **only family A members** — typing `lena` or `ira`
    yields nothing.
13. Repeat 11–12 mirrored as Lena.

## Phase 5 — Protected media (known surface, record what you see)

14. As Lena, copy the full URL of her avatar or of the family B gallery photo
    (from the page source or "copy image address").
15. As Nora, paste that URL. **Expect (current code)**: the file **is**
    served — `download_protected_media` (core/views/views_general.py) checks
    login only, not the tenant. This is an **observed deviation to record**
    (media are auth-gated, not tenant-gated); classify it as accepted
    limitation or defect depending on the family's data policy. Anonymous
    access must still be refused (login redirect).

## Phase 6 — Auth boundaries and the deactivated family

16. As Nora, open family B's home `http://localhost:8000/isolation-family-ifb/`.
    **Expect**: redirect to the site home (authenticated users have no
    business on another family's public home page) — no branding, no join
    button for B.
17. As SU, deactivate family B: `/tenants/isolation-family-ifb/toggle-active/`.
    Then, as Lena, request any page. **Expect**: session ended with message
    *"This space has been deactivated and can no longer be accessed."*
    (TenantMiddleware logs out on inactive tenant); `/<slug_b>/` and
    `/members/login/` as Lena lead nowhere. Family A is untouched: Nora keeps
    working normally while B is off. Re-activate B as SU afterwards.

## Phase 7 — Superuser is unscoped (by design, verify only)

18. As SU: `/tenants/` lists both families; `/admin/members/member/` shows
    members of both families with their tenant. This cross-tenant visibility
    is **expected** for the platform admin — the check is only that it stays
    confined to SU sessions: log back in as Nora and confirm Phase 1 lists
    are still scoped.

## Pass criteria

- Every tenant-scoped list shows only the current family's rows (Phase 1).
- Every cross-tenant access by pk/slug/username is denied — 404 expected,
  403/redirect acceptable; **no 200 with the other family's data, no 500**
  (Phases 2–4).
- Member search/follow/birthdays never cross the family line (Phase 3).
- The protected-media observation is recorded explicitly as deviation or
  accepted limitation (Phase 5).
- Deactivation of a family locks its members out without touching others
  (Phase 6); superuser cross-tenant powers stay confined to SU sessions
  (Phase 7).

## Note

Automated coverage exists for parts of this (`members/tests/
tests_tenant_isolation.py`, per-app `TenantModel` tests). This scenario is
the browser-level mirror: it exercises real sessions, real slugs and real
media URLs end to end.
