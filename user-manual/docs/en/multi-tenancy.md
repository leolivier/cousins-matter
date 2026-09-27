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

## Connecting to a family

Everyone logs in on the standard login page — the family is resolved
automatically from the logged-in account; there is no per-family URL. An email
address belongs to a single family: to join another family, you need another
address.

* **Family creator**: after signing up at *"Create a new family"*, the account
  is inactive until the verification email link is clicked; then log in
  normally and you are the family's admin.
* **Other members**: either accept the invitation emailed by the family admin
  (tenant-bound link → signup → email verification), or submit a join request
  (captcha form) that a family admin must approve. In both cases, log in on
  the standard login page afterwards.

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
make the database itself refuse cross-tenant writes. RLS is active when
`MULTI_TENANT_ENABLED=True` **and** `POSTGRES_RUNTIME_USER` is set.

**With Docker**, set in `.env`:

```
MULTI_TENANT_ENABLED=True
POSTGRES_RUNTIME_USER=cm_app
POSTGRES_RUNTIME_PASSWORD=<strong password>
```

then restart the app containers:

```
docker compose restart cousins-matter qcluster
```

On startup the entrypoint runs the migrations **as the owner**
(`POSTGRES_USER`): the RLS migration (`tenants.0003_rls`) creates the runtime
role with DML-only grants and applies the policies, then the server and
qcluster restart and connect as the runtime role. Nothing to run by hand.

**With a manual (non-Docker) install**, set the same variables and run
`manage.py migrate` **as the owner** (`POSTGRES_USER`) — this is exactly what
the entrypoint automates above.

**What `POSTGRES_USER` is for**: it is the owner (superuser) created by the
PostgreSQL image. It runs the migrations — creating the runtime role, its
DML-only grants and the policies — and as the owner it bypasses RLS entirely,
which is why `FORCE ROW LEVEL SECURITY` is never used. The server and qcluster
only fall back to it when `POSTGRES_RUNTIME_USER` is unset (RLS then has no
effect).

How the policies behave for the runtime role:

* all tenant-scoped tables (galleries, chat, forum, classified ads, polls,
  troves, genealogy, pages): rows outside the session's tenant are invisible
  **and** unwritable;
* `members_member`: reads stay permissive (login by email happens before a
  tenant is known), but INSERT/UPDATE/DELETE are hard-scoped;
* the middleware sets `app.current_tenant_id` per request and always resets
  it afterwards (pooled connections never leak a tenant); platform superusers
  get `app.bypass` so they can administer cross-tenant;
* migrations run as the owner, which bypasses RLS — this is intended, and the
  reason `FORCE ROW LEVEL SECURITY` is never used.

## Current scope

All product apps are tenant-scoped and covered by row-level security:
`members`, `galleries`, `chat`, `troves`, `forum`, `classified ads`, `polls`,
`genealogy` and `pages` — 22 tables, migrations `tenants.0003_rls` through
`tenants.0010_rls_pages`. Only infrastructure tables (Django sessions, allauth
accounts) remain global; the ORM scoping applies to everything else.
