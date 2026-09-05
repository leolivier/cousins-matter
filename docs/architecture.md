---
type: Architecture
title: Architecture
description: How the Django project is wired — settings selection, middleware, ASGI/Channels, static and media serving, Docker topology
tags: [architecture, settings, asgi, docker]
status: draft
stale_after: 2027-03-04
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T21:36:13Z }
---

# Architecture

## Project module and settings

`manage.py` sets `DJANGO_SETTINGS_MODULE` to `core.settings` (`manage.py`) — the settings entry
point lives in the `core` app, not in a project-level `settings/` package. `core/settings.py`
reads the `ENVIRONMENT` environment variable (default `production`) and dispatches with a
`match` statement:

| `ENVIRONMENT` | Settings module | Use |
|---|---|---|
| `development` | `config/settings/development.py` | local dev server |
| `production` | `config/settings/production.py` | deployed instances (default) |
| `test` | `config/settings/local_test.py` | unit + UI tests (`make test`, `make cover`) |
| `docker-devt` | `config/settings/docker_devt.py` | containers started by `make up` / `make up4run` |
| `docker-test` | `config/settings/docker_test.py` | tests inside the container (`make dtest`) |

Any other value raises `ValueError` (`core/settings.py`). All variants import
`config/settings/base.py` (or `config/settings/dev_base.py`, itself importing base) via
`from ... import *`.

Facts that hold in every environment:

- `config/settings/base.py` loads `.env` with django-environ and requires `SECRET_KEY`
  (a dummy default exists in `dev_base.py` only).
- `LOCAL_APPS` (`config/settings/base.py`): `core`, `tenants`, `members`, `chat`, `galleries`,
  `classified_ads`, `cousinsmatter`, `forum`, `genealogy`, `pages`, `polls`, `troves`.
  `cousinsmatter` is the project module (settings/ASGI/urls), not a feature app.
- `AUTH_USER_MODEL = "members.Member"` (`config/settings/base.py`).
- Database is PostgreSQL only (`config/settings/base.py` `DATABASES`), with an RLS-oriented
  runtime-user switch: when `MULTI_TENANT_ENABLED` is true the app connects as
  `POSTGRES_RUNTIME_USER`, while migrations run as the table owner (see
  `scripts/entrypoint.py`).
- `MULTI_TENANT_ENABLED` (default `False`) is the product feature flag for multi-tenancy;
  `DEFAULT_TENANT_SLUG` and `SYSTEM_TENANT_SLUG` are defined next to it. See
  [/specs/multi-tenancy.md](/specs/multi-tenancy.md).

## Middleware

Order from `MIDDLEWARE` in `config/settings/base.py`. Development and docker-devt prepend
`debug_toolbar.middleware.DebugToolbarMiddleware` when `DEBUG_TOOLBAR` is enabled (default on
in `config/settings/development.py`, opt-in in `config/settings/docker_devt.py`).
`core.htmlvalidator.HtmlValidatorMiddleware` is available but NOT wired in: the
`MIDDLEWARE.append(...)` lines for it are commented out in `config/settings/local_test.py`,
`config/settings/development.py` and `config/settings/docker_devt.py`, so it appears in no
active chain:

1. `django.middleware.security.SecurityMiddleware`
2. `django.middleware.csp.ContentSecurityPolicyMiddleware` (policy built in
   `config/settings/base.py`: `SECURE_CSP` enforced, `SECURE_CSP_REPORT_ONLY` during rollout)
3. `whitenoise.middleware.WhiteNoiseMiddleware`
4. sessions, locale, CORS, common, CSRF, authentication
5. `allauth.account.middleware.AccountMiddleware`
6. messages
7. `tenants.middleware.TenantMiddleware` — resolves the current family/tenant
8. `core.middleware.LoginRequiredMiddleware` — every URL requires login except
   `LOGIN_REQUIRED_IGNORE_PATHS` (`config/settings/base.py`: `/static/`, `/captcha/`,
   `/accounts/...`, `/i18n/`, `/robots.txt`, ...)
9. `XFrameOptionsMiddleware`, `FlatpageFallbackMiddleware`
10. `django_htmx.middleware.HtmxMiddleware`

## ASGI and Channels

`cousinsmatter/asgi.py` builds `application` as a `ProtocolTypeRouter`: HTTP goes to
`get_asgi_application()`, websockets to
`AuthMiddlewareStack(URLRouter(chat.routing.websocket_urlpatterns))`. `django.setup()` is
forced before importing `chat.routing` (comment in the file). `"daphne"` is first in
`INSTALLED_APPS` and `ASGI_APPLICATION = "cousinsmatter.asgi.application"`
(`config/settings/base.py`). The channel layer is
`channels_redis.core.RedisChannelLayer` pointed at `REDIS_HOST`/`REDIS_PORT`, with
`socket_timeout: None` and retry/health-check options (see the commented rationale in
`config/settings/base.py` — do not replace the dict with a plain `(host, port)` tuple).

## URL surface

`cousinsmatter/urls.py` includes each app's urls (`core/`, `members/`, `posts/` (forum),
`chat/`, `galleries/`, `polls/`, `genealogy/`, `pages-edit/`, `troves/`,
`classified-ads/`), plus `admin/`, `accounts/` (allauth), `i18n/`, `captcha/`, `verification/`,
flatpages under `settings.PAGES_URL_PREFIX`, and `health/` / `qhealth/` views from
`core/views/views_general.py`. The `tenants/` include is appended only when
`settings.MULTI_TENANT_ENABLED` is true.

## Static and media

- Static files: WhiteNoise. `STORAGES["staticfiles"]` is
  `whitenoise.storage.CompressedManifestStaticFilesStorage`, collected into `STATIC_ROOT`
  (`static/`, `config/settings/base.py`). Test settings swap in plain
  `StaticFilesStorage` so tests run without `collectstatic`
  (`config/settings/local_test.py`, `config/settings/docker_test.py`).
- Protected media: `MEDIA_URL = "/protected_media/"` (`config/settings/base.py`) and
  `MEDIA_ROOT = media/`. Downloads go through the `download_protected_media` view in
  `core/views/views_general.py`, routed in `cousinsmatter/urls.py` — never link a protected
  file directly.
- Public media: `PUBLIC_MEDIA_ROOT = MEDIA_ROOT / "public"` (filesystem `media/public/`),
  served at `PUBLIC_MEDIA_URL = "/public_media/"` through `download_public_media`
  (`cousinsmatter/urls.py`).
- Only the `public` storage alias can be reconfigured to a remote backend via the
  `MEDIA_STORAGE` / `MEDIA_STORAGE_OPTIONS` env vars; `default` stays local
  (FileSystemStorage on `MEDIA_ROOT`) (`config/settings/base.py`).

## Async tasks

Django-Q2 (`django-q2` in `pyproject.toml`). `Q_CLUSTER` in `config/settings/base.py` uses
Redis and `"sync": env.bool("Q_SYNC", False)`; `config/settings/dev_base.py` flips the
default to `True` so tasks run synchronously in development and tests. The `qcluster`
process runs as its own container (below).

## Docker topology

`docker-compose.yml` defines five services on the `cousins_matter_network` bridge:

- `cousins-matter` — the ASGI app image (`ghcr.io/leolivier/cousins-matter`), health-checked
  by `scripts/healthcheck.py`.
- `qcluster` — same image, command `python manage.py qcluster`.
- `postgres` — `postgres:18.2-alpine`, data in the `cousins_matter_postgres_data` volume.
- `redis` — used by both Channels and Django-Q2.
- `nginx` — reverse proxy serving `static/` and `media/`, exposing port 8000.

`scripts/entrypoint.py` initializes the app container: it takes a leadership lock in Redis,
checks `.env`/`SECRET_KEY`, and on first run creates media directories and `theme.css`, then
runs `migrate`, `collectstatic`, creates the superuser from env vars, and finally execs the
container command.

# See also

- [Conventions](/conventions.md) — services pattern, custom user model, feature flags
- [Development Setup](/setup-dev.md) — running the stack locally
- [Testing](/testing.md) — test commands and environments
- [Multi-Tenancy spec](/specs/multi-tenancy.md)
- User manual: [settings](https://cousins-matter.readthedocs.io/settings/),
  [installation](https://cousins-matter.readthedocs.io/installation/),
  [reverse proxying](https://cousins-matter.readthedocs.io/reverse-proxying/)
