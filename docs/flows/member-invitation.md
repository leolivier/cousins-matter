---
type: Flow
title: Member Invitation
description: End-to-end invitation flow — who may invite, the signed registration link, the invitee's registration, email verification and activation
tags: ["flow", "members"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T11:39:00Z }
---

# Member Invitation

There is no open sign-up: a new member gets in either through an invitation
link sent by an authorized member, or (optionally) through a registration
request reviewed by an admin. This flow covers the invitation path end to
end. The moving parts (Member model, tenant scoping, forms) are described in
[Members](/apps/members.md) and [Tenants](/apps/tenants.md).

## Steps

1. **Inviter opens the form.** `GET /members/register/invite`
   (members/urls.py, `name="invite"`) →
   `members/views/views_registration.py: MemberInvitationView.get` renders
   `members/registration/registration_invite.html` with a
   `members/forms.py: MemberInvitationForm` (`invited` name + `email`).
   A `?mail=` query param pre-fills the email (used by the registration
   *request* flow below).
2. **Authorization gate.** `MemberInvitationView.check_before_invitation`
   allows superusers, tenant admins (`Member.is_tenant_admin`) and, when the
   per-tenant setting `allow_members_to_invite_members` is on, plain
   members of the tenant (`tenants/settings_overrides.py` maps it to the
   `ALLOW_MEMBERS_TO_INVITE_MEMBERS` env default, editable per tenant in the
   tenant settings form). Otherwise: `PermissionDenied` → 403.
3. **Inviter submits.** `MemberInvitationView.post` validates the form, then
   rejects an email that already exists in `Member` ("A member with this email
   already exists"). No DB write on rejection.
4. **Signed link generation.**
   `members/registration_link_manager.py: RegistrationLinkManager.generate_link`
   builds the payload `"<tenant_id>:<email>"` (tenant-prefixed so the target
   tenant is covered by the HMAC and cannot be swapped in the URL), signs it
   with `TokenManager.make_token` (salted HMAC over `SECRET_KEY` + base36
   timestamp), base64-encodes the payload, and returns the absolute URL
   `/members/register/<encoded_email>/<token>`.
5. **Invitation email.** The view renders
   `members/email/registration_invite_email.html` and `send_mail`s it to the
   invitee from `settings.DEFAULT_FROM_EMAIL`. **Side effect:** if the inviter
   is not the tenant's designated admin (first of
   `tenants/authz.py: admin_or_superusers`), a second email
   (`registration_sent_email.html`) warns that admin. Then a success message
   is flashed and the form is re-rendered. **No member row is created yet.**
6. **Invitee opens the link.** `GET /members/register/<encoded>/<token>` →
   `members/views/views_registration.py: RegistrationCheckingView.get` →
   `check_before_register` →
   `RegistrationLinkManager.decrypt_link` (base64-decode + `check_token`).
   On success the view stores `invitation_token`, `invitation_email` and
   `invitation_tenant_id` in the session (reused by the OAuth flow, see
   [OAuth Login](/flows/oauth-login.md)) and renders
   `MemberRegistrationForm` + address/family forms.
7. **Registration submit.** `RegistrationCheckingView.post` re-checks the
   link, then — inside `tenants/scoping.py: tenant_context(<invitation
   tenant>)`, because the request is anonymous and no middleware tenant
   exists — calls `verify_email.email_handler: send_verification_email`,
   which saves the new `Member` **with `is_active=False`** and emails a
   verification link. **Side effects:** Member row created on the invitation's
   tenant (subject to the `member_tenant_username_uniq` uniqueness on
   `(tenant, username)`), one verification email, session keys set.
8. **Email verification / activation.** Clicking the verification email link
   flips `is_active=True` (handled by the `verify_email` package). As a
   fallback, a manager can activate the member manually through
   `members/views/views_member.py: activate_member`
   (`/members/<username>/activate/`). End state: an active member who can log
   in by email (`ACCOUNT_LOGIN_METHODS = {"email"}`).

## Variant: registration request (no invitation yet)

An anonymous visitor at `GET/POST /members/register/request`
(`members/views/views_registration.py: RegistrationRequestView`) fills
`members/forms.py: RegistrationRequestForm` — including a captcha — and the
message is emailed to the first **active superuser**
(`Member.unscoped.filter(is_superuser=True, is_active=True)`; anonymous
request → tenant unknown → platform admin). No member row is created; the
admin then invites the requester from step 1 (the email to the admin carries
the invite URL).

## Failure modes visible to the user

- Link expired or tampered (`TokenManager.check_token`, max age
  `MAX_REGISTRATION_AGE`, config/settings/base.py: 2 days by default):
  "Invalid link. Please contact the administrator." and redirect home.
- Email already registered and **active**: "A member with the same email
  address is already active. Please sign in instead".
- Email registered but **inactive**: "You are already registered but not
  active. Please contact <manager> to activate your account" (manager =
  `Member.member_manager`).
- Inviting without the rights: 403.
- Duplicate email at invitation time: error message, no email sent.
- Emails here are plain synchronous `django.core.mail.send_mail` calls (not
  Django-Q2 tasks — unlike follower notifications): a broken SMTP config
  raises inside the request.

## Related

- [Members app](/apps/members.md) — model, forms, CSV import as a bulk alternative.
- [Tenants app](/apps/tenants.md) — tenant scoping and `tenant_context`.
- [OAuth Login flow](/flows/oauth-login.md) — same invitation consumed via a social provider.
