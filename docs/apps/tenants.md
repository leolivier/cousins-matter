---
type: App Reference
title: Tenants
description: Shared-schema multi-tenancy — Tenant/TenantSettings models, thread-local scoping, TenantMiddleware, RLS hardening, per-tenant settings and authz helpers
tags: ["app", "tenants"]
status: draft
stale_after: 2027-03-04
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T22:06:02Z }
---

# Tenants

`tenants` implements multi-tenancy (several families on one deployment) with a
**shared schema**: every tenant-scoped row carries a `tenant` FK, isolation is
enforced first by the ORM (tenant-scoped managers) and backstopped by
PostgreSQL row-level security. This fiche documents the code; the
product-level behaviour lives in user-manual/multi-tenancy.md and the design
rationale in [Multi-tenancy spec](/specs/multi-tenancy.md).

The whole feature is gated by `MULTI_TENANT_ENABLED`
(`env.bool`, default `False`, config/settings/base.py). The middleware is
always installed, but the `/tenants/` URLs and the runtime-role DB switch only
exist when the flag is on.

## Tenant vs Family

Two words, two levels:

- `tenants.models.Tenant` is the **isolation boundary**: one family/site per
  deployment. `TenantSettings` hangs off it.
- `members.models.Family` (members/models.py) is a grouping of members
  *inside* a tenant (name + optional parent family) — it plays no role in
  isolation. Confusingly, the self-service signup view is named
  `FamilySignupView` because "create a family" is the user-facing phrasing for
  "create a tenant".

## Models (tenants/models.py)

- `Tenant` — `name`, unique `slug` (max 63), `is_active`, timestamps.
  Two slugs are special, both `env.str`-configurable
  (config/settings/base.py): `DEFAULT_TENANT_SLUG` (`"default"`) is where
  rows land when no tenant can be resolved (management commands, legacy data),
  and `SYSTEM_TENANT_SLUG` (`"system"`) hosts the cross-tenant platform
  superusers (`create_superuser` assigns it, members/managers.py); it can
  never be deleted (`Tenant.is_system`, `tenants.services.delete_tenant`).
  Instances resolved by slug are memoized in `_tenant_cache`; the memo is
  reset on `post_migrate` and `setting_changed` so tests that flush tables
  don't keep stale pks.
- `TenantSettings` — `OneToOneField(Tenant)` plus an `overrides` JSONField
  (feature flags, branding). `tenant_settings_overrides(tenant=None)` returns
  the raw dict (defaulting to the current tenant), `{}` when there is none.
- `_seed_tenants_post_migrate` re-creates the default/system tenants after
  `migrate` **and** after `TransactionTestCase.flush`, mirroring what Django
  does for content types.

## Scoping primitives (tenants/scoping.py)

- A thread-local holds the current tenant: `get_current_tenant()` /
  `set_current_tenant()`.
- `tenant_context(tenant)` activates it for a block — the way Django-Q
  workers, management commands and tests get a tenant that the middleware
  would otherwise provide. It also drives the RLS session variable.
- `TenantManager.get_queryset()` filters by the current tenant when one is
  active and leaves the queryset unfiltered otherwise (authentication lookups,
  `createsuperuser`, migrations). `TenantModel` is the abstract base for
  scoped models: non-editable `tenant` FK, scoped `objects` manager,
  `unscoped` escape hatch, and `ensure_tenant()` auto-assignment on `save()`
  (falling back to the default tenant).
- `Member` deliberately does **not** inherit `TenantModel`: it owns the FK
  that identifies the tenant and redeclares it with its own save() fallback
  (members/models.py, members/managers.py).

## TenantMiddleware (tenants/middleware.py)

Listed unconditionally in `MIDDLEWARE` (config/settings/base.py). For each
request it resolves the tenant from the logged-in member's `user.tenant` and
activates it (`set_current_tenant`, `request.tenant`):

- a member whose tenant has been deactivated is logged out with a message and
  bounced to the login page (no redirect loop: the next request is anonymous);
- platform superusers are left unscoped and get `set_rls_bypass(True)`;
- anonymous requests stay unscoped so allauth can resolve a user by email
  before any tenant is known.

The `finally` block always `reset_rls()` and restores the previous
thread-local tenant, so a pooled connection never carries a stale tenant or
bypass flag into the next request.

## RLS hardening (tenants/rls.py)

Defense-in-depth behind the ORM layer. `rls_enabled()` requires
`MULTI_TENANT_ENABLED` **and** a `POSTGRES_RUNTIME_USER` **and** the
PostgreSQL engine. When enabled, `set_rls_tenant` /
`set_rls_bypass` / `reset_rls` manage the session variables
`app.current_tenant_id` and `app.bypass` that the policies read. Policies are
created by migration `tenants.0003_rls` for the non-owner runtime role:

- `TENANT_RLS_STRICT_TABLES` (`galleries_gallery`, `galleries_photo`) — a
  strict `FOR ALL` policy: rows outside the session tenant are invisible and
  unwritable;
- `TENANT_RLS_SPLIT_TABLES` (`members_member`) — permissive `SELECT` (login by
  email must read cross-tenant before the tenant is known) but hard-scoped
  writes;
- extend `TENANT_RLS_TABLES` when converting another app to `TenantModel`.

The table owner (used for migrations, see scripts/entrypoint.py) always
bypasses RLS — policies are therefore never `FORCE`d. When the feature is on,
`DATABASES["default"]["USER"]` switches to the runtime role
(config/settings/base.py); migrations keep running as the owner.

## Authorization helpers (tenants/authz.py)

- `is_platform_admin(user)` — authenticated `is_superuser` (cross-tenant).
- `is_tenant_admin(user, tenant=None)` — superuser, or `Member.role ==
  "admin"` on that tenant (defaults to the current one; the middleware
  guarantees a non-superuser's request is scoped to their own tenant).
- `tenant_admins(tenant)` — active `role="admin"` members of the tenant
  (unscoped); the replacement for the old "first superuser" lookups.
- `admin_or_superusers(tenant)` — those admins, or all active platform
  superusers as fallback; the standard recipient list for admin emails.

## Per-tenant settings (tenants/settings_overrides.py)

`TENANT_SETTINGS_SPEC` declares the only keys that may be overridden per
tenant (site_name, site_logo, site_copyright, site_footer, pdf_size,
dark_mode, language_code, time_zone, birthday_days,
allow_members_to_create_members, allow_members_to_invite_members,
family_chart_root_person_id), each mapped to the global Django setting used as
default. `tenant_setting(key)` returns override → global → default;
`effective_overrides(tenant=None)` returns all of them, memoized and cleared
by `clear_tenant_settings_cache()`. Everything not in the spec is never read
per tenant.

## Cache keys (tenants/caching.py)

`tenant_cache_key(key)` prefixes `"t:<tenant pk>:"` when a tenant is active,
so per-tenant computed values (charts, feature sets) cannot leak across
tenants through the shared cache.

## Views and URLs

`tenants/urls.py` (`app_name = "tenants"`) is mounted at `/tenants/` only when
`MULTI_TENANT_ENABLED` (cousinsmatter/urls.py):

- `family_signup/` — `FamilySignupView` (tenants/views/views_signup.py):
  anonymous self-service creation of a new tenant; inside
  `transaction.atomic` it creates `Tenant` + `TenantSettings` and the creator
  as an inactive `role="admin"` member, then sends the verification email
  under `tenant_context`. Throttled per IP through the cache
  (`SIGNUP_THROTTLE_LIMIT` submissions per `SIGNUP_THROTTLE_SECONDS`).
- `settings/` — `TenantSettingsUpdateView` (tenants/views/views_settings.py):
  form over `TENANT_SETTINGS_SPEC`; restricted to platform superusers and
  tenant admins (`PermissionDenied` otherwise).
- list / `create/` / `<slug>/toggle-active/` / `<slug>/delete/` —
  `TenantListView`, `TenantCreateView`, `TenantToggleActiveView`,
  `TenantDeleteView` (tenants/views/views_manage.py): platform-superuser only
  (`OnlySuperuserMixin`), and every view is guarded by
  `multi_tenant_required` (tenants/views/__init__.py) which 404s when the
  feature is off. Creating a tenant can send an admin invitation.

Deletion goes through `tenants.services.delete_tenant`, which refuses the
system tenant and still-active tenants (deactivate first), deletes the
tenant's members explicitly (`Member.tenant` is `PROTECT`) and lets
tenant-scoped rows cascade; it returns the number of members removed.

# See also

- [Multi-tenancy spec](/specs/multi-tenancy.md) — design rationale and roadmap
- [Members](/apps/members.md) — `Member.tenant`, `Member.role`, invitation links
- [Core](/apps/core.md) — feature flags and `{{ settings }}` overrides
- [Architecture](/architecture.md) — middleware order, settings selection
- user-manual/multi-tenancy.md — enabling and administering families
