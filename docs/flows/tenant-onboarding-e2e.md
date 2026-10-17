---
type: Flow
title: Tenant Onboarding E2E (Manual Test)
description: Manual end-to-end test scenario — family self-signup, first tenant admin, managed member creation, join request, invitation, registration and login
tags: ["flow", "tenants", "members", "testing", "manual"]
status: draft
stale_after: 2027-04-17
generated: { by: claude-code/glm-5.3-flash, at: 2026-10-17T00:00:00Z }
---

# Tenant Onboarding E2E (Manual Test)

A manual, click-through test scenario covering the full tenant (family)
onboarding: a family is created by self-service signup, its creator becomes
the first tenant admin, the admin creates a managed member, an outsider
requests to join, the tenant admin answers with an invitation, the invitee
registers, activates and logs in.

Only `/tenants/signup/` (`FamilySignupView`, `tenants/views/views_signup.py`)
assigns `role=ADMIN` automatically, so self-service signup is the main path
tested here. The platform path `/tenants/create/` is covered as a known gap
at the end.

Related: [Member Invitation](/flows/member-invitation.md) (mechanics of the
signed link), [Tenants](/apps/tenants.md), [Members](/apps/members.md).

## Preconditions

- `.env` has `MULTI_TENANT_ENABLED=True` (otherwise `/tenants/` URLs 404).
- `make up4run` (postgres/redis) then `make run` → app on `http://localhost:8000`.
- Dev emails print to the `make run` terminal (console email backend): copy
  activation/invitation links from there. The join form shows a captcha that
  must be typed.
- A platform superuser account exists (SU, for Django-admin observations only).

## Actors / test data

| ID | Who | Email | Notes |
|----|-----|-------|-------|
| SU | Platform superuser | pre-existing | only for `/admin/` observations |
| A1 | Family creator → tenant admin | `nora@example.com` | |
| M1 | Managed member created by A1 | e.g. `marta@example.com` | stays inactive |
| R1 | Outside requester → invited | `hugo@example.com` | uses a private window |

## Phase 0 — Environment

1. Check `MULTI_TENANT_ENABLED=True` in `.env`; start `make up4run` then
   `make run`; open `http://localhost:8000`. Log out if needed.

## Phase 1 — Family self-creation (tenant creation)

2. Browse `http://localhost:8000/tenants/signup/`. **Expect**: two sections —
   a family form (name) and the member registration form.
3. Fill family name `Test Family ETA`; registration: username `nora`, first
   name, email `nora@example.com`, birthdate, password. Submit.
4. **Expect**: success message *"Your family has been created! You will now
   receive an email to verify your email address…"*, redirect to the login
   page. (Internally: `Tenant` + `TenantSettings` created, slug auto-derived
   `test-family-eta`; member `nora` with `role=admin`, inactive.)
5. In the `make run` terminal, open the verification email for
   `nora@example.com` and click its activation link. **Expect**: activation
   confirmation page.

## Phase 2 — First login as tenant admin

6. Log in at `/members/login/` with **email** `nora@example.com` + password
   (login is by email, `ACCOUNT_LOGIN_METHODS = {"email"}`).
7. **Expect**: authenticated home. Admin powers visible:
   - `/members/register/invite` loads (not 403);
   - `/tenants/settings/` loads (per-family settings form);
   - `/tenants/` (families list) is **403** — tenant admins must not manage
     the tenant lifecycle.

## Phase 3 — Admin creates a managed member

8. As Nora: Members page → *Create member* (or direct `/members/create/`).
   Fill the form (username `marta`, names, birthdate…). Submit.
9. **Expect**: flash *"Member successfully created"*, redirect to Marta's
   detail page. In `/admin/members/member/`: row `marta` with **is_active
   unchecked** and **member_manager = Nora** (`CreateManagedMemberView` →
   `do_init_member` forces `is_active=False` + `member_manager=admin`).
10. Negative check: a login attempt with `marta@example.com` is refused
    (account inactive).

## Phase 4 — Join request from an outsider

11. In a **private window** (anonymous), open the family home
    `http://localhost:8000/test-family-eta/`. **Expect**: family branding
    (site name override), *Sign in* link and a join-request button (the join
    link appears on the family home only, not the global login page).
12. Click the join button → `/test-family-eta/join/`. Fill: name `Hugo`,
    email `hugo@example.com`, message, type the captcha. Submit.
13. **Expect**: flash *"Registration request sent."* + redirect to the family
    home. In the terminal: email *"Registration request for \<site\>"*
    addressed to the tenant admin (Nora, via `tenants/authz.py:
    admin_or_superusers`), containing name/email/message and an **"Open
    invitation page"** button → `/members/register/invite?mail=hugo@example.com`.

## Phase 5 — Tenant admin answers the request

14. As Nora, click that button. **Expect**: invitation form with email
    **pre-filled** `hugo@example.com`. Type invited name `Hugo`, submit.
15. **Expect**: flash *"Invitation sent to hugo@example.com."*, the form
    re-renders and shows the shareable family home URL. No member row created
    yet (optional check in `/admin/`). Terminal: invitation email to Hugo
    with a signed link `/members/register/<encoded>/<token>`.

## Phase 6 — Registration of the invited person

16. Private window: open the link from the invitation email. **Expect**:
    *Sign up* form (registration + address + family sections). Fill username
    `hugo`, password, etc. Submit.
17. **Expect**: flash *"Hello hugo, your account has been created!…"*,
    redirect to login. Terminal: verification email for Hugo — click its
    link → activated.

## Phase 7 — Login of the new member

18. Log in with **email** `hugo@example.com` + password. **Expect**: Hugo
    lands on the family-scoped site, authenticated, no permission errors on
    the members pages.

## Edge checks (optional)

- Expired/tampered invitation link → *"Invalid link. Please contact the
  administrator."* + redirect home (max age 2 days, `MAX_REGISTRATION_AGE`).
- Join request with an email that already exists → *"A member with this email
  already exists."*
- Slug collision: create a second family with the same name → slug becomes
  `<slug>-2`; a reserved slug is rejected.
- After deactivating the family (`/tenants/<slug>/toggle-active/` as SU),
  `/<slug>/` and `/<slug>/join/` return 404 and members can't sign in.

## Known gap (observed deviation)

- Platform path `/tenants/create/` (as SU) with `admin_email`: the invited
  person can register, but ends with `role=member` — they get **no**
  tenant-admin powers (cannot open `/tenants/settings/` nor
  `/members/register/invite`); `role` is not editable in the Django member
  admin. Record as a defect/known limitation if exercised.

## Pass criteria

All numbered expectations in Phases 0–7 hold; at minimum: tenant + admin
created via self-signup, admin can create a managed member (inactive,
managed), join request reaches the tenant admin by email, admin invitation
pre-filled and sent, invitee registers, activates and logs in on the family
site.
