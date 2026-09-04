---
type: App Reference
title: Members
description: The custom user model, families and addresses, managed members, invitations and registration links, CSV import/export, following
tags: ["app", "members"]
status: draft
stale_after: 2027-03-04
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T12:00:00Z }
---

# Members

`members` owns the custom Django user model and everything that revolves around
people: their profile, their family grouping, who manages whom, how they sign up
(invitation or self-service) and who follows them.

## The `Member` model

`Member` (members/models.py) extends `django.contrib.auth.models.AbstractUser`
and is declared as `AUTH_USER_MODEL = "members.Member"` (config/settings/base.py).
Always resolve it with `django.contrib.auth.get_user_model()`, never import it in
`settings.py`.

Fields that matter beyond `AbstractUser`:

- `role` — `Member.Role` text choices: `member` (default) and `admin`
  ("Tenant admin"). `Member.is_tenant_admin` is the property form; cross-tenant
  platform admins are plain `is_superuser`, not a role.
- `tenant` — non-editable FK to `tenants.Tenant`, `on_delete=PROTECT`
  (see [Tenants](/apps/tenants.md)).
- `member_manager` — self FK (`related_name="managed_members"`): the account that
  manages this (inactive) member. `get_manager()` returns the manager, or the
  member itself when it manages itself.
- `family` — FK to `Family` (below), plus `address` FK to `Address`.
- `birthdate`, `is_dead` / `deathdate`, `phone`, `website`, `avatar`,
  `description`, `hobbies`, `privacy_consent`.
- `followers` — M2M to `"self"`, `symmetrical=False`,
  `related_name="following"`.
- `email_batch_frequency` — one of `FREQUENCY_NEVER`, `FREQUENCY_IMMEDIATE`
  (default), `FREQUENCY_HOURLY`, `FREQUENCY_DAILY`, `FREQUENCY_WEEKLY`,
  `FREQUENCY_MONTHLY`; consumed by the notification batcher
  (see [Core](/apps/core.md) and [Followers](/modules/followers.md)).

Username handling is unusual: `username` is redeclared with `unique=False` and
uniqueness becomes a `UniqueConstraint` on `(tenant, username)`
(`member_tenant_username_uniq`), so the same username may exist in two tenants.
Login is by email; `USERNAME_FIELD` stays `"username"` and
`REQUIRED_FIELDS = ["first_name", "last_name", "birthdate", "email"]`.

Model behaviour worth knowing:

- `save()` (members/models.py) assigns the tenant first —
  `get_current_tenant()` or, when none is active (management commands,
  `createsuperuser`, allauth signup), `Tenant.get_default()` — then runs
  `clean()`, then regenerates avatar thumbnails only when the avatar file
  actually changed (a login touching `last_login` must not rewrite files).
- `clean()` derives `is_dead`/`is_active` from `deathdate`, clears
  `member_manager` on active members, and assigns one to inactive members
  without one: the first active tenant admin of the member's tenant, falling
  back to any platform superuser (lookups use `unscoped` because `objects` is
  tenant-filtered).
- `delete()` removes the avatar files only after the row deletion succeeded.

`LoginTrace` (members/models.py) records login IP / user agent / geolocation;
it is populated by signal handlers in members/trace_login.py, imported for their
side effects by `MembersConfig.ready` (members/apps.py).

## Managers

`MemberManager` (members/managers.py) is tenant-aware:
`get_queryset()` filters by `tenants.scoping.get_current_tenant()` and is left
unfiltered when no tenant is active (anonymous requests, management commands,
platform superusers) so authentication lookups keep working. `Member.unscoped`
is the plain-manager escape hatch for explicit cross-tenant access.

- `create_member(...)` defaults `is_active=False` and resolves the tenant.
- `create_superuser(...)` forces `is_staff`, `is_superuser`, `role="admin"` and
  `tenant=Tenant.get_system()` — superusers live on the *system* tenant.
- `alive()` / `dead()` filter on `is_dead`.
- `fuzzy_search(query)` uses `TrigramSimilarity` on the concatenated name.

## Family and Address

`Family` (members/models.py) is a named grouping with an optional `parent`
family (self FK) — it organises members *inside* a tenant and is **not** the
isolation boundary; that is `tenants.Tenant`
(see [Tenants](/apps/tenants.md)). `Address` holds postal fields and is shared
by members through a nullable FK. Both have standard CRUD views plus HTMX modal
variants (members/views/views_family.py, members/views/views_address.py).

## Managed members

A *managed member* is an inactive `Member` whose `member_manager` is another
account: the manager fills the profile, then activates it.

- `CreateManagedMemberView` (members/views/views_member.py) creates the member;
  `do_init_member` (members/services/members.py) forces `is_active=False` and
  sets `member_manager` to the logged-in user.
- `activate_member` → `do_activate_member` (members/services/members.py)
  refuses dead, already-active or email-less members, otherwise sends the
  verification email (`verify_email.email_handler.send_verification_email`);
  the owner finishes with the password-reset screen.

## Invitations and registration links

`RegistrationLinkManager` (members/registration_link_manager.py, subclass of
`TokenManager`) builds one-time links signed with `salted_hmac` over
`SECRET_KEY` (salt `cousinsmatter.members.check_before_registry.TokenManager`),
valid for `MAX_REGISTRATION_AGE` (default 2 days, config/settings/base.py).
The payload is `"<tenant_id>:<email>"` when the invite is tenant-bound, so the
tenant is covered by the HMAC and cannot be swapped in the URL.

Flow (members/views/views_registration.py):

1. `MemberInvitationView` (`members:invite`) — allowed to platform/tenant
   admins, or to anyone when `tenant_setting("allow_members_to_invite_members")`
   is on. Generates the tenant-bound link for the invitee's email
   (`RegistrationLinkManager.generate_link` with `request.user.tenant_id`) and
   emails it.
2. `RegistrationCheckingView` (`members:register/<encoded_email>/<token>`) —
   verifies the link via `decrypt_link`, refuses logged-in or already-active
   members, and stores `(invitation_token, invitation_email,
   invitation_tenant_id)` in the session before showing the signup form.
3. `RegistrationRequestView` (`members:register_request`) — captcha-protected
   self-service request; the request email goes to the first active platform
   superuser (the request is anonymous, so no tenant is known yet).

Social login is wired through `CustomSocialAccountAdapter`
(members/adapter.py): `pre_social_login` validates the session invitation with
`RegistrationLinkManager.check_invitation`, then either links and activates the
existing inactive member or allows allauth to create the signup with
`is_active=True` and the invitation's `tenant_id` — no invitation, no signup.

## CSV import / export

- Import: `CSVImportView` (members/views/views_import_export.py) →
  `do_import_members_from_csv` (members/services/import_export.py) validates
  the header (`check_fields` against `ALL_FIELD_NAMES`, members/models.py) and
  dispatches **one Django-Q task per row** —
  `async_task("members.tasks.import_row", ...)`, grouped under a UUID. The
  `ImportContext` carries the importer's `tenant_id` into the worker, which has
  no request/middleware. Progress is polled through
  `get_import_progress` (`count_group` / `result_group`) via the
  `import_progress` view.
- Row handling helpers live in members/tasks.py: `manage_avatar`,
  `manage_family`, `get_valid_manager`, `handle_managed_by`, `update_address`,
  `create_member` / `update_member`.
- Export: `select_members_to_export` → `export_members_to_csv` →
  `do_export_members_to_csv` (filterable by name, family, city).

## Following

`Member.followers` / `following` is the people-to-people graph.
`toggle_follow` (members/views/views_followers.py) → `do_toggle_follow`
(members/services/members.py) adds/removes the edge and emails the followed
member (`members/email/new_follower.html`). Following of *content* (chat rooms,
posts, ...) is a separate generic mechanism documented in
[Followers](/modules/followers.md).

## Permissions

Per-family roles are two-level by design: `Member.role == "admin"` administers
the member's own tenant, `is_superuser` administers every tenant. The shared
helpers (`is_platform_admin`, `is_tenant_admin`, `tenant_admins`,
`admin_or_superusers`) live in tenants/authz.py and are documented in
[Tenants](/apps/tenants.md). View-level checks (`_can_edit_member`) are in
members/views/views_member.py.

# See also

- [Tenants](/apps/tenants.md) — the isolation boundary behind `Member.tenant`
- [Followers](/modules/followers.md) — generic follow/notification machinery
- [Core](/apps/core.md) — batched notification emails, protected media
- [Architecture](/architecture.md) — middleware order (TenantMiddleware, login required)
- user-manual/features.md — member-facing feature tour
- user-manual/settings.md — `ALLOW_MEMBERS_TO_*` settings
