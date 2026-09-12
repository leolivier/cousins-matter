# Multi-tenancy (several families on one deployment)

Cousins Matter can serve **several families (tenants) from a single deployment**,
with every family's data isolated. This page documents the product feature and
its deployment.

## Enabling the feature

The feature is **off by default**: a single-family deployment behaves exactly
like the classic app. To turn it on, set in `.env`:

```
MULTI_TENANT_ENABLED=True
```

This mounts the `/tenants/` URLs (family signup + management) and shows the
"Create a new family" link on the login page. When off, all of this 404s.

## Concepts

| Concept | Where |
|---|---|
| **Family (tenant)** | `tenants.Tenant` — name, slug, `is_active` |
| **Family admin** | `Member.role = "admin"` — manages their family's members and settings |
| **Platform admin** | `is_superuser` — cross-tenant, lives on the `system` tenant, Django-admin (`is_staff`) access |
| **Isolation (primary)** | tenant-scoped ORM manager (`TenantManager`) + `TenantMiddleware` |
| **Isolation (backstop)** | PostgreSQL row-level security (see below) |

Two tenants are seeded by migration and cannot be deleted: `default`
(assigned when none can be resolved) and `system` (home of platform admins).

## Creating a family

* **Self-service**: with the feature on, the login page offers
  *"Create a new family"*. The creator signs up with email verification and
  becomes the family's admin.
* **By a platform admin**: `/tenants/create/` creates the family and can email
  an invitation (tenant-bound link) to its first admin.

A family identifier (slug) is derived from its name; reserved slugs
(`default`, `system`, `admin`, …) are rejected.

## Family settings

A family admin edits their family's settings at **Family settings**
(navbar dropdown): site name, logo, copyright, footer, dark mode, PDF page
size, language, time zone, birthday lookahead, member permissions
(create/invite), and the genealogy chart root. Values equal to the global
defaults are **not stored**, so a global change still propagates to families
that never overrode them. Emails to "the admin" (contact form, invitations,
death notifications) are routed to the **family's admin**.

## Lifecycle

* **Deactivate** (`/tenants/<slug>/toggle-active/`): the family's members are
  logged out and cannot sign in until reactivation.
* **Hard delete** (`/tenants/<slug>/delete/`, or `manage.py delete_tenant
  <slug>`): permanently removes the family and all its data. Refuses the
  system tenant and any still-active family; requires typing the slug.

## PostgreSQL row-level security (optional hardening)

The ORM scoping is the primary isolation layer. For defense-in-depth, you can
make the database itself refuse cross-tenant writes:

1. Pick a non-owner role, e.g. `cm_app`, with a strong password.
2. In `.env`, set `POSTGRES_RUNTIME_USER` / `POSTGRES_RUNTIME_PASSWORD` (and
   keep `MULTI_TENANT_ENABLED=True`).
3. Run `manage.py migrate` **as the owner** (`POSTGRES_USER`) — the RLS
   migration (`tenants.0003_rls`) creates the role, grants DML-only privileges
   and the policies. The container entrypoint does this automatically:
   initialization runs as the owner, only the long-running server uses the
   runtime role.

How the policies behave for the runtime role:

* tenant-scoped tables outside the apps' own models (galleries): rows outside
  the session's tenant are invisible **and** unwritable;
* `members_member`: reads stay permissive (login by email happens before a
  tenant is known), but INSERT/UPDATE/DELETE are hard-scoped;
* the middleware sets `app.current_tenant_id` per request and always resets
  it afterwards (pooled connections never leak a tenant); platform superusers
  get `app.bypass` so they can administer cross-tenant;
* migrations run as the owner, which bypasses RLS — this is intended, and the
  reason `FORCE ROW LEVEL SECURITY` is never used.

## Current scope

Today `members` and `galleries` are tenant-scoped. Converting the remaining
apps (chat, forum, polls, classified ads, pages, troves, genealogy) follows
the same pattern (`TenantModel` base + composite indexes); until then those
apps' data is shared across families of a deployment.
