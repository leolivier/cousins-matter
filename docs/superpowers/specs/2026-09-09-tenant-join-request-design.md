# Design: Tenant-scoped join request (registration request redesign)

Date: 2026-09-09
Status: approved design, pending implementation plan
Branch: `feature/tenant-join-request`

## Context

In the multi-tenant fork, the tenant of a request is resolved from the logged-in
member (`tenants/middleware.py`); anonymous requests run unscoped
(`request.tenant = None`). Consequences:

- Anonymous pages cannot display any family identity (`tenant_setting()` falls
  back to global settings), so a "request an invitation" entry point placed on
  global pages has no family to belong to.
- The current `RegistrationRequestView` (`members/views/views_registration.py`)
  emails the **first platform superuser** with a link to `members:invite` that
  requires login and prefills nothing. Superusers do not manage tenants or
  accounts, so the feature is structurally broken in the multi-tenant model.

The feature is redesigned from scratch. Three decisions validated with the user:

1. **Entry point: per-family public URL space.** Each family gets a public page
   at `/<tenant slug>/` showing the tenant's unauthenticated home — the same
   page anonymous visitors saw before multi-tenancy (the login page), with the
   family's branding. From there, the "request invitation" link opens the
   family's join form (`/<slug>/join/`), pre-scoped to that tenant; the request
   email goes to that tenant's admins. On unscoped pages the global entry point
   is hidden while multi-tenancy is enabled — and served by the same code via
   the default tenant when it is disabled (see "Tenant resolution").
2. **Family page reuses the existing anonymous page.** `/<slug>/` delegates to
   the exact same `LoginView` as `members:login`
   (`django.contrib.auth.views.LoginView`, template
   `members/login/login.html`), so it behaves identically to the current
   unauthenticated page (login form, language, password reset), only
   tenant-scoped via `request.tenant`.
3. **Admin action: prefilled invite form.** The request email contains a
   `members:invite?mail=<email>` link; the admin logs in, confirms, and the
   existing signed, tenant-bound invitation flow takes over unchanged.
4. **One code path, flag or no flag.** `MULTI_TENANT_ENABLED=False` does not
   keep a legacy implementation: the same views run, resolving the **default
   tenant**. User-visible behavior stays the same (see the explicit delta list
   in "Tenant resolution"), and single-tenant deployments exercise exactly the
   code multi-tenant ones do.

## Behavior

### GET/POST `/<slug>/` (route `tenant-home`) — family unauthenticated home

- 404 when the slug is unknown or the tenant is inactive.
- Sets `request.tenant = tenant` and wraps dispatch in `tenant_context(tenant)`:
  the `settings` context processor (`core/context_processors.py`) then layers the
  family's overrides, so navbar/site name/logo are the family's. This is the
  family-branded anonymous page that was previously impossible.
- Delegates to the exact same `LoginView` as `members:login` (same template,
  `members/login/login.html`), handling GET **and** POST so the login form works
  from the family URL without any change to authentication (login is global).
- On this page the unauthenticated navbar/login template shows the
  "Request invitation link" entry, pointing to `/<slug>/join/`. The link is
  rendered conditionally (`{% if request.tenant %}`), so unscoped pages
  (`/accounts/login/`, global root) never show it.

### GET/POST `/<slug>/join/` (route `tenant-join`) — join request form

- Same tenant resolution rules: 404 unknown/inactive slug, tenant context set.
- Renders the existing `RegistrationRequestForm` (name, email, message, captcha).

### POST (join form)

Same view, in order:

1. Captcha must pass (existing form field).
2. Throttle: 5 submissions/hour/IP, cache-based (`_throttled` pattern,
   reimplemented locally in `members` — see "Upstream contribution" below).
3. Email must not already belong to a member — checked against
   `Member.unscoped` (login email is global). This also fixes a latent bug: the
   current check uses the tenant-scoped manager, which is empty for anonymous
   requests.
4. Sends one email to **all active admins of the tenant**
   (`tenants/authz.tenant_admins`, falling back to platform superusers), with:
   family name, requester name/email/message, and an absolute
   `members:invite?mail=<email>` link.
5. Success: existing "request sent" message + redirect back to the family home
   (`tenant-home`, same slug).

### Tenant resolution — one code path, flag or no flag

The same views serve both modes; only tenant resolution differs:

- `MULTI_TENANT_ENABLED=True`: the slug in the URL selects the tenant.
- `MULTI_TENANT_ENABLED=False`: the **default tenant** (`Tenant.get_default()`)
  is used. The legacy `/members/register/request` URL is kept as an alias of
  `tenant-join` — same view, same `members:register_request` name — resolving
  to the default tenant. `/<slug>/` and `/<slug>/join/` 404 for any tenant
  other than the default: a no-tenant deployment has exactly one family.

Observable differences for flag-off users (explicit, all benign):

1. Recipients: `tenant_admins(default_tenant)` with superuser fallback — all
   active superusers instead of only the first. No visible change with the
   usual single-admin deployment.
2. The duplicate-email check now actually runs (unscoped manager); previously
   the tenant-scoped check silently passed for anonymous requests.
3. After a successful request the user lands on the family home (the login
   page) instead of `/`.

Everything else — URL, form, captcha, links on login/navbar, email content —
is unchanged.

No invitation is ever generated without a logged-in admin: the power to invite
stays behind authentication, and invitation links remain signed and
tenant-bound (`RegistrationLinkManager`).

## Components

| File | Change |
|---|---|
| `cousinsmatter/urls.py` | Append, **last** (the home route is a catch-all), always mounted — no flag gating in the URLconf: `tenant-join` = `"<slug:slug>/join/"` then `tenant-home` = `"<slug:slug>/"`, both routed to the new views. |
| `tenants/views/views_home.py` (new) | `TenantHomeView`: tenant resolution + scoping, then delegates to the same `LoginView` as `members:login` (GET and POST). |
| `members/views/views_registration.py` | Replace `RegistrationRequestView` with `TenantJoinRequestView`: tenant from URL slug, or default tenant when reached via the legacy alias / flag off; throttle. Send logic stays inline, consistent with the sibling `MemberInvitationView`. |
| `members/templates/members/email/registration_request_email.html` | Rework: family name, requester info, prefilled invite link. |
| `members/templates/members/registration/registration_request.html` | Show the family name; adjusted copy. |
| `members/templates/members/registration/registration_invite.html` | Add one line showing the family's shareable home URL (`/<slug>/`). |
| `core/templates/core/unauthenticated-navbar.html` | "Request invitation" link kept but contextual: `tenant-join` with the tenant slug when `request.tenant` is set; legacy `members:register_request` when `not settings.MULTI_TENANT_ENABLED`; hidden otherwise. |
| `members/templates/members/login/login.html` | Same contextual rule for its "Request invitation link" link. |
| `tenants/forms.py` (`uniquify_tenant_slug`) | Reject reserved first segments — the first segment of every root route (`admin`, `accounts`, `members`, `posts`, `chat`, `galleries`, `polls`, `genealogy`, `password`, `captcha`, `i18n`, `health`, `qhealth`, `tenants`, `saas`, `troves`, `classified-ads`, `pages-edit`, `robots.txt`) plus `static`, `media`, `protected-media` — so a tenant can never shadow an existing root route. |

`members/urls.py` keeps its `register/request` path and `members:register_request`
name but points them at the unified view (alias resolving to the default
tenant), so existing bookmarks and links keep working with one implementation.

Translations: new/changed strings require `make mkmsg a=members` (+ `core` if
navbar strings change), then translated `.po` updates.

## Security & error handling

- Captcha kept; per-IP throttle added (anonymous mail-sending endpoint).
- Unknown/inactive slug → 404.
- Flag off: `/<slug>/` and `/<slug>/join/` 404 for any tenant other than the
  default — no hidden multi-tenant surface when tenancy is off.
- The `tenant-home` catch-all is appended **after** every existing include, so
  real routes always win; unknown slugs 404 inside the view (still a 404).
  Reserved slugs are rejected at tenant creation (`uniquify_tenant_slug`).
- No tenant admins → superuser fallback (existing helper); superuser-less
  deployments keep the existing "unable to send mail" error path.
- `send_mail` failure → existing error message.

## Testing

- Flag-off regression through the unified view: `/members/register/request`
  keeps working (same form, same links, default tenant branding); the request
  email reaches all active superusers (not just the first); `/<slug>/` URLs of
  non-default tenants return 404. Tests asserting the global link run with
  `MULTI_TENANT_ENABLED=False` (override), since the link hides when the flag
  is on.
- New join-flow tests (flag on): family branding on GET, 404 for
  unknown/inactive slug, email delivered to tenant admins (and not to
  superusers when admins exist), duplicate email rejected via unscoped check,
  throttle.
- New `tenants` tests for `tenant-home`: renders the login page with family
  branding, login POST succeeds from `/<slug>/`, "request invitation" link
  visible there but absent on `/accounts/login/`, 404 for unknown/inactive slug.
- Flag-off routing: `/<slug>/` and `/<slug>/join/` work for the default tenant
  and 404 for any other tenant when the flag is off.
- Reserved-slug rejection test in `tenants` tests.

## Docs (OKF bundle rule)

- Update `docs/apps/members.md` (and `core` fiche if navbar strings change);
  bump `stale_after`; `make check-docs` must pass.

## Upstream contribution (cousins-matter)

This behavior belongs at cousins-matter level, not in the cmm fork:

- Every touched piece is upstream code (`core`, `members`, `tenants`); the
  design must work on a stock cousins-matter checkout.
- No dependency on cmm-only apps (`saas`): the per-IP throttle is
  reimplemented locally in `members` — the saas `_throttled` pattern is
  inspiration only, never an import.
- Implementation happens on this fork's branch; once validated it is
  contributed to `upstream/main` via PR (fork workflow: origin = fork,
  upstream = cousins-matter).
- Flag-off deployments run the exact same code via the default tenant — one
  code path for stock upstream deployments, no fork-specific legacy branch.

## Out of scope

- Tenant-scoped branding of the global login page.
- The SaaS landing / tenant-creation flow (`saas` app) — unchanged, stays
  cmm-specific.
