---
type: Feature Spec
title: OAuth Authentication
description: Design of env-driven social login — provider config built at import time, invitation-gated signup in the social adapter, and how a social signup lands on the right tenant
tags: ["spec", "oauth"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T12:02:12Z }
---

# OAuth Authentication

Social login is delegated to `django-allauth`; the project-specific design
decisions are (1) providers configured from the environment with **no
database state**, and (2) signup gated by the same invitation mechanism as
email registration, enforced in one adapter hook. Provider setup and
troubleshooting live in user-manual/oauth-authentication.md; the request
round-trip is traced in [OAuth Login](/flows/oauth-login.md).

## Configuration model (config/settings/base.py ~582-621)

`OAUTH_PROVIDERS` is a comma-separated list of provider names. At **import
time** the settings module, for each name:

- appends `allauth.socialaccount.providers.<app>` to `INSTALLED_APPS`;
- builds `SOCIALACCOUNT_PROVIDERS[app]["APPS"]` from
  `<NAME>_OAUTH_CLIENT_ID` and `<NAME>_OAUTH_CLIENT_SECRET`;
- for OpenID Connect additionally reads `<NAME>_SERVER_URL` (used for both
  `server_url` and `issuer`), forces `token_auth_method =
  "client_secret_post"` and `oauth_pkce_enabled = True`.

The name `pocketid` is a special case mapping to the `openid_connect` provider
app; any other OpenID Connect provider just uses its own name. Consequences:

- there are **no `SocialApp` rows** — the provider list cannot be edited at
  runtime, and changing `.env` requires a process restart (that is why the
  user manual ends with "restart required");
- a provider name in `OAUTH_PROVIDERS` without its `_OAUTH_CLIENT_ID`/`_SECRET`
  env vars fails at startup (`env.str` with no default), which is deliberate
  fail-fast rather than a half-configured login button.

## The invitation gate (members/adapter.py)

`SOCIALACCOUNT_ADAPTER = members.adapter.CustomSocialAccountAdapter`. Its
`pre_social_login` hook runs after the provider round-trip, before allauth
creates or connects anything, and enforces the invariant **no invitation, no
account**:

- no email from the IdP → error message + redirect to login
  (`ImmediateHttpResponse`); the email is the only join key.
- The pending invitation is the session triple `(invitation_token,
  invitation_email, invitation_tenant_id)` set when the invitee clicked their
  link; it is validated by
  `RegistrationLinkManager.check_invitation(email, tenant_id, token)` and
  **popped on use** — an invitation is single-shot per social login.
- Existing member with that email: `is_active` → plain login, no DB change;
  inactive + valid invitation → `sociallogin.connect()` + `is_active=True`;
  inactive without one → bounced with the "not yet active" message.
- Unknown email + valid invitation → the new member is allowed through with
  `is_active=True` **and `tenant_id` taken from the invitation**.

That last point is the tenant-design keystone: the request is anonymous and
therefore **unscoped** (see [Multi-Tenancy](/specs/multi-tenancy.md)), so the
only source of truth for where a social signup belongs is the invitation's
tenant carried through the session.

## Related invariants

- `SOCIALACCOUNT_AUTO_SIGNUP` defaults to `False`: the user confirms the
  email on a local form instead of being logged in blindly;
  `list_providers` sets `confirm_login` accordingly.
- `ACCOUNT_EMAIL_VERIFICATION = "none"` — there is no local verification step
  for social logins; the invitation check *is* the verification.
- `ACCOUNT_LOGIN_METHODS = {"email"}` pairs with the per-tenant username
  uniqueness described in the multi-tenancy spec; `auth.W004` is silenced for
  the same reason.
- The signup form is swapped (`SOCIALACCOUNT_FORMS =
  members.forms.MemberSocialSignupForm`) so provider signups populate the
  Member profile fields (first/last name, birthdate), not Django's bare user.
- OAuth never bypasses `Member.is_active`: activation happens exclusively
  through the invitation path, and a deactivated tenant's members are logged
  out by `TenantMiddleware` regardless of how they authenticated.

# See also

- [OAuth Login](/flows/oauth-login.md) — step-by-step round trip
- [Members](/apps/members.md) — invitations, `RegistrationLinkManager`
- [Multi-Tenancy](/specs/multi-tenancy.md) — unscoped anonymous requests, tenant placement
- user-manual/oauth-authentication.md — per-provider setup and troubleshooting
