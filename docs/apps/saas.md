---
type: App Reference
title: SaaS
description: Public landing + self-service tenant requests (captcha, signed email link, auto-created tenant + admin, onboarding checklist) — the SaaS front door of the cmm fork
tags: ["app", "saas"]
status: draft
stale_after: 2027-03-07
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-07T00:00:00Z }
---

# SaaS

`saas` is the only app added by the **cmm fork** (private fork of
cousins-matter): it turns a multi-tenant deployment into a public SaaS
front door — "create your family site" — while upstream apps stay
untouched (merge-friendly: the only upstream contact points are a handful
of lines in `config/settings/base.py`, `cousinsmatter/urls.py`,
`core/views/views_general.py`, `core/templates/core/base.html`,
`members/templates/members/login/login.html` and
`core/context_processors.py`).

The whole feature is gated by `SAAS_LANDING_ENABLED` (`env.bool`, default
`False`, config/settings/base.py): when off, no `/saas/` URLs are mounted
and the home page behaves normally.

## Flow

1. **Landing** — `HomeView` (core/views/views_general.py) renders
   `saas/landing.html` instead of the regular home when the flag is on and
   the visitor is anonymous; the login page "Create a new family" link
   points to `saas:signup`.
2. **Request** — `SignupRequestView` (saas/views/views_signup.py): family
   name + email, protected by Cloudflare Turnstile
   (`saas/turnstile.py`, server-side `siteverify`, fails closed; no-op
   while `TURNSTILE_ENABLED` is off) and an IP throttle (5 requests/h,
   same policy as `tenants.views.views_signup`). Emails of existing
   members are refused (global email login). Creates a `TenantRequest`
   (platform table, not tenant-scoped) and sends a signed link.
3. **Validation** — `TenantValidateView` (saas/views/views_validate.py):
   GET on the signed link (`saas/tokens.py`,
   `TenantRequestTokenManager` subclassing members' `TokenManager`, max
   age `SAAS_TENANT_REQUEST_MAX_AGE`, via
   `services.resolve_tenant_request`) shows a confirmation page — a GET
   never mutates; POST re-checks the link and calls
   `services.create_tenant_from_request`, which in one transaction creates
   `Tenant` (slug from `uniquify_tenant_slug`, `-2` suffix on collision),
   `TenantSettings` and the `Member` admin (active, unusable password,
   `role="admin"`), marks the request `VALIDATED`, then the view auto-logs
   the admin in
   (explicit `ModelBackend`: multi-backend setup) and redirects to
   `saas:welcome`. Expired/played/tampered links mark the request
   `EXPIRED` and bounce to the signup.
4. **Welcome** — `WelcomeView`: stock `SetPasswordForm`
   (`update_session_auth_hash` keeps the session alive) + intro.
5. **Onboarding** — `saas/onboarding.py` computes the checklist state on
   the fly (password set? profile filled? other members on the tenant?);
   rendered on every page through an inclusion tag in
   `core/templates/core/base.html`, only for tenant admins who have not
   dismissed it. `saas:onboarding_dismiss` stores
   `saas_onboarding_done` in `TenantSettings.overrides`.

## Model (saas/models.py)

`TenantRequest` — `email`, `tenant_name` (200), `status`
(`PENDING`/`VALIDATED`/`EXPIRED`), `expires_at` (set from
`SAAS_TENANT_REQUEST_MAX_AGE` at creation), `validated_at`, `ip`. No FK
to `Tenant` (the slug is only computed at validation), no stored token
(the link is stateless HMAC).

## Purge + schedule (saas/services.py)

`purge_tenant_requests()` deletes expired `PENDING` requests and resolved
(`VALIDATED`/`EXPIRED`) ones past 30 days retention; exposed as
`manage.py purge_tenant_requests` and scheduled daily via django-q2
(schedule created on post_migrate like core's notification schedules).
`saas/admin.py` exposes `TenantRequest` for platform support.

## Settings (config/settings/base.py)

| Setting | Default | Role |
|---|---|---|
| `SAAS_LANDING_ENABLED` | `False` | master flag: landing + `/saas/` URLs |
| `SAAS_TENANT_REQUEST_MAX_AGE` | `86400` | signed-link validity (s) |
| `SAAS_DEMO_URL` | cousins-matter.levillain.eu | demo link on the landing |
| `SAAS_DOCS_URL` | readthedocs | docs/self-hosting link |
| `TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY` | `""` | Turnstile keys |
| `TURNSTILE_ENABLED` | on iff both keys set | server verification on/off |

CSP (same file, `_CSP_POLICY`): `https://challenges.cloudflare.com` is
allowed in `script-src`, `frame-src` and `connect-src`, otherwise the
widget does not load. `LOGIN_REQUIRED_IGNORE_PATHS` includes `/saas/`.

Deployment note: cousins-matter.net is a deployment value (DNS +
`ALLOWED_HOSTS`), nothing to code.

## Internationalization

User-facing strings are English with `gettext` like every other app;
`fr`/`es`/... catalogues for `saas` are not generated yet (`make mkmsg
a=saas && make cpmsg a=saas` when needed).

# See also

- [Tenants](/apps/tenants.md) — `Tenant`/`TenantSettings`, scoping, signup throttle reused here
- [Members](/apps/members.md) — `Member`, `TokenManager` reused for the signed links
- user-manual/multi-tenancy.md — product view (see "SaaS hosting" section)
- `docs/spec.md` — product spec this app implements
