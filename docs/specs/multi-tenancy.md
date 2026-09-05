---
type: Feature Spec
title: Multi-Tenancy
description: Design rationale and invariants of shared-schema multi-tenancy — isolation layers (ORM scoping, RLS backstop), the default/system tenants, per-tenant settings, and the known gaps
tags: ["spec", "multi-tenancy"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T12:02:12Z }
---

# Multi-Tenancy

One deployment serves several families. The design goal was to get real
isolation **without** schema-per-tenant or database-per-tenant operational
cost, so the chosen model is **shared schema**: one database, one set of
tables, and a `tenant` foreign key on every tenant-scoped row. Product-level
behaviour (enabling, signup, lifecycle) lives in user-manual/multi-tenancy.md;
the code tour is [Tenants](/apps/tenants.md). This fiche states the
invariants those pages only point at.

## The two isolation layers

1. **ORM scoping (primary).** `TenantManager.get_queryset()`
   (tenants/scoping.py) filters by the thread-local current tenant; models
   inheriting `TenantModel` get it as `objects`, auto-assign `tenant` on
   `save()` (`ensure_tenant()`, falling back to the default tenant), and keep
   an `unscoped` manager as the explicit escape hatch. `Member` re-declares
   the same behaviour itself (members/managers.py) because it owns the FK that
   *defines* the tenant. The current tenant comes from `TenantMiddleware`
   (HTTP) or `tenant_context()` (Django-Q, commands, tests).
2. **PostgreSQL RLS (backstop).** Active only when
   `MULTI_TENANT_ENABLED=True` **and** `POSTGRES_RUNTIME_USER` is set **and**
   the engine is PostgreSQL (`tenants/rls.py: rls_enabled()`). Policies read
   the session variables `app.current_tenant_id` / `app.bypass`; the
   middleware and `tenant_context()` set them, and always `RESET` them in a
   `finally` so pooled connections never leak a tenant.

Neither layer alone is trusted: ORM scoping is bypassable by a forgotten
`unscoped` call, RLS is bypassable by the table owner. Hence both.

## RLS enforcement points (invariants)

- Policies are created by migration `tenants/migrations/0003_rls.py`, which is
  idempotent, elidable, and a no-op on non-PostgreSQL. It creates the runtime
  role (`NOSUPERUSER`, DML-only grants) only when
  `POSTGRES_RUNTIME_USER`/`POSTGRES_RUNTIME_PASSWORD` are configured;
  otherwise the `ENABLE ROW LEVEL SECURITY` statements still run — inert,
  because the app connects as the table owner.
- The owner always bypasses RLS, so policies are never `FORCE`d. That is why
  migrations keep running as `POSTGRES_USER` while web + qcluster switch to
  the runtime role (`DATABASES["default"]["USER"]` in config/settings/base.py,
  and scripts/entrypoint.py which initializes as owner).
- Two policy shapes: `TENANT_RLS_STRICT_TABLES` (`galleries_gallery`,
  `galleries_photo`) get a strict `FOR ALL` policy — foreign rows invisible
  *and* unwritable; `members_member` gets split policies with permissive
  `SELECT` (login-by-email and admin lookups must read before any tenant is
  known) but tenant-scoped `INSERT`/`UPDATE`/`DELETE`.
- **Known gap:** the RLS table list lags `TenantModel` adoption. `chat`
  (`ChatRoom`, `ChatMessage`) is ORM-scoped but has no RLS policy yet —
  extend `TENANT_RLS_TABLES` in tenants/rls.py when hardening it (its own
  comment still lists chat as "to convert", which is stale).

## Identity invariants

- `username` is unique per **(tenant, username)** only
  (`member_tenant_username_uniq`, members/models.py); Django's
  `auth.W004` (globally unique `USERNAME_FIELD`) is silenced in
  config/settings/base.py. Login is by email (`ACCOUNT_LOGIN_METHODS`).
- `email` carries **no** uniqueness constraint: it is the cross-tenant
  identity key that login and `CustomSocialAccountAdapter` resolve before a
  tenant is known — making it unique would break that lookup.
- Platform superusers live on the `system` tenant (`create_superuser` assigns
  `Tenant.get_system()`) and are deliberately left unscoped, with
  `app.bypass='on'`.

## Reserved tenants

`default` (`DEFAULT_TENANT_SLUG`) and `system` (`SYSTEM_TENANT_SLUG`) are
seeded by data migration `tenants/migrations/0002_seed_tenants.py` and
re-created after `migrate` **and** after `TransactionTestCase.flush` by the
`post_migrate` hook in tenants/models.py — mirroring Django's content types.
Resolved instances are memoized in `_tenant_cache`, invalidated on
`post_migrate`/`setting_changed` (flush between tests would otherwise leave
stale pks). The system tenant can never be deleted
(`tenants/services.py: delete_tenant` refuses it, and refuses still-active
tenants — deactivate first; `Member.tenant` is `PROTECT`, so members are
deleted explicitly before the cascade).

## Per-tenant settings

`TENANT_SETTINGS_SPEC` (tenants/settings_overrides.py) is an **allow-list**:
only its keys (branding, pdf_size, dark_mode, language_code, time_zone,
birthday_days, member creation/invitation permissions,
family_chart_root_person_id) are ever read per tenant, each falling back
override → global Django setting → default. Everything else in
`django.conf.settings` stays global by design. Values are memoized per
(tenant, globals) and cleared by `clear_tenant_settings_cache()`; cache keys
for per-tenant computed values are prefixed `t:<pk>:` via
`tenants/caching.py: tenant_cache_key` so the shared cache cannot leak across
tenants.

## What is *not* tenant-scoped

Media files carry no tenant prefix on disk or in any backend — file
isolation is access-control at the view layer, not storage layout (see
[Media Storage](/specs/media-storage.md)). Static assets are global. URLs are
not tenant-prefixed: the tenant is always derived from the session, never
from the hostname or path.

# See also

- [Tenants](/apps/tenants.md) — the code: models, middleware, views
- [Media Storage](/specs/media-storage.md) — why media is outside the tenant scope
- user-manual/multi-tenancy.md — enabling, family lifecycle, RLS setup recipe
- [Architecture](/architecture.md) — middleware order, settings selection
