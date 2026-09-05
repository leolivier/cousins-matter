---
type: Flow
title: OAuth Login
description: End-to-end social login — provider configuration from env, the allauth round trip, and how a pending invitation is consumed by the social adapter
tags: ["flow", "oauth"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T11:39:00Z }
---

# OAuth Login

Social login is delegated entirely to `django-allauth`; the project-specific
part is one adapter (`members/adapter.py`) that lets a **pending invitation**
([Member Invitation](/flows/member-invitation.md)) be consumed through a
social provider instead of the emailed verification link. The adapter is
summarized in [Members](/apps/members.md); the `TenantSettings.overrides`
layer behind tenant settings like `allow_members_to_invite_members` is
described in [Modules/Feature flags](/modules/feature-flags.md).

## Configuration (config/settings/base.py)

- `INSTALLED_APPS` includes `allauth`, `allauth.account`,
  `allauth.socialaccount` (+ one provider app per configured provider, added
  at startup); `allauth.account.middleware.AccountMiddleware` is in the
  middleware list; templates override `members/templates/allauth/`.
- Providers are **env-driven only** — no `SocialApp` rows in the DB:
  `OAUTH_PROVIDERS` is a list of provider names; for each, the settings block
  builds `SOCIALACCOUNT_PROVIDERS[app]["APPS"]` from
  `<NAME>_OAUTH_CLIENT_ID`, `<NAME>_OAUTH_CLIENT_SECRET` and, for
  OpenID Connect, `<NAME>_SERVER_URL` (with PKCE and
  `client_secret_post`). The special name `pocketid` maps to the
  `openid_connect` provider app.
- `SOCIALACCOUNT_AUTO_SIGNUP = False` by default: after the provider
  round-trip the user confirms the email on a local form rather than being
  logged in blindly; `list_providers` in the adapter sets
  `confirm_login = True` accordingly.
- `SOCIALACCOUNT_ADAPTER = "members.adapter.CustomSocialAccountAdapter"`,
  `SOCIALACCOUNT_FORMS = {"signup": "members.forms.MemberSocialSignupForm"}`
  (the Member profile fields), and `ACCOUNT_LOGIN_METHODS = {"email"}`.

## Steps

1. **Entry point.** The login page offers the provider buttons; they hit
   `/accounts/<provider>/login/` — cousinsmatter/urls.py:
   `path("accounts/", include("allauth.urls"))`. Anonymous access works
   because `core/middleware.py: LoginRequiredMiddleware` exempts the
   allauth URL roots (its whole reason for overriding the stock middleware).
2. **Provider round trip.** Allauth redirects to the provider and handles the
   callback `/accounts/<provider>/login/callback/`.
   `ACCOUNT_EMAIL_VERIFICATION = "none"` disables any local email
   verification step — the adapter's invitation checks (step 3) are the only
   gate.
3. **Adapter hook.** Before any account is created or connected, allauth
   calls `members/adapter.py: CustomSocialAccountAdapter.pre_social_login`:
   - **No email from the provider** → error message
     ("The identity provider did not provide an email address.") and
     redirect to login (`ImmediateHttpResponse`).
   - **Existing member with that email, `is_active`** → return; allauth
     proceeds with a normal login. No DB change.
   - **Existing member, inactive** → `_check_invitation` validates the
     session-stored invitation (below). Valid →
     `sociallogin.connect(request, member)`, `member.is_active = True`,
     save (the member keeps its own tenant); invalid → "This account is not
     yet active. Please use the invitation link sent to you by email."
   - **No member yet** → valid session invitation → the new
     `sociallogin.user` is marked `is_active = True` and placed on
     `invitation_tenant_id` (the request is anonymous, so no middleware
     tenant exists); invalid → "No invitation found for this email address.
     Please request an invitation first."
4. **Where the invitation comes from.** The invitee must first have opened
   their email invitation link once:
   `members/views/views_registration.py: RegistrationCheckingView.get`
   stores `invitation_token` / `invitation_email` / `invitation_tenant_id`
   in the session. `_check_invitation` re-signs
   `"<tenant_id>:<email>"` and validates it with
   `members/registration_link_manager.py:
   RegistrationLinkManager.check_invitation` (same HMAC + 2-day
   `MAX_REGISTRATION_AGE` as the link itself), then pops the three session
   keys — the invitation is single-use.
5. **Account creation / signup form.** Because
   `SOCIALACCOUNT_AUTO_SIGNUP` is False, a brand-new email lands on the
   social signup form (`MemberSocialSignupForm`: profile fields + privacy
   consent); submitting it creates the `Member` with the values staged in
   step 3. End state: an **active** `Member` on the invitation's tenant, an
   allauth `SocialAccount` row linking it to the provider identity, and the
   user logged in.

## Side effects

- DB writes: `Member` row (new-signup case), `SocialAccount` row on
  connect/signup, `is_active` flip (inactive-member case).
- Session: the three invitation keys are consumed and removed.
- No email is sent by this flow (unlike the email-link path).

## Failure modes visible to the user

- Provider does not return an email claim → error + redirect to login.
- Invitation missing, expired (> `MAX_REGISTRATION_AGE`, 2 days default) or
  for a **different email** than the one the provider returns → "No
  invitation found…" (new account) or "not yet active…" (existing inactive
  account). Social login can never create or activate an uninvited account.
- Provider misconfigured (bad client id/secret/server URL) → allauth's
  provider error page.
- Username collisions at signup surface through the form's validation —
  uniqueness is `(tenant, username)` (`member_tenant_username_uniq`), scoped
  to the invitation's tenant.

## Related

- [Member Invitation flow](/flows/member-invitation.md) — where the session
  invitation comes from.
- [Members app](/apps/members.md) — `Member` model, login by email.
- [Tenants app](/apps/tenants.md) — how the anonymous signup lands on the
  right tenant.
