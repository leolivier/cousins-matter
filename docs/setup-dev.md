---
type: Setup
title: Development Setup
description: Get a local development environment running — uv, Docker containers, migrations and translations
tags: [setup, makefile, uv, docker]
status: draft
stale_after: 2027-03-04
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T21:36:13Z }
---

# Development Setup

## Prerequisites

- Python >= 3.14 (`requires-python` in `pyproject.toml`)
- [uv](https://docs.astral.sh/uv/) for dependency management
- Docker + Docker Compose for PostgreSQL, Redis and the qcluster worker
- A `.env` file at the repo root — `config/settings/base.py` reads it with django-environ and
  requires `SECRET_KEY`

## Install dependencies

```bash
uv sync --dev
source .venv/bin/activate
```

`--dev` installs the `dev` dependency group from `pyproject.toml` (ruff, mypy, bandit,
coverage, playwright, ...). The project code itself runs from the repo root with
`./manage.py` (which sets `DJANGO_SETTINGS_MODULE=core.settings`).

## Start the backing services

```bash
make up4run   # alias: make u4r
```

This runs `docker compose up -d postgres redis qcluster` with `ENVIRONMENT=docker-devt`
(`Makefile`), i.e. the PostgreSQL, Redis and Django-Q2 services from `docker-compose.yml`.

## Run the dev server

```bash
make run      # ./manage.py runserver — http://localhost:8000
```

`config/settings/dev_base.py` sets `SITE_PORT = 8000` and `SITE_DOMAIN = localhost`;
`make run` itself is plain `./manage.py runserver` (`Makefile`), so Django's default port 8000
applies.

## Migrations

```bash
make mkmig    # ENVIRONMENT=development ./manage.py makemigrations
make mig      # ENVIRONMENT=development ./manage.py migrate
```

## Translations

```bash
make mkmsg a=<app>   # makemessages -a inside the app
make cpmsg a=<app>   # compilemessages inside the app
```

## Choosing `ENVIRONMENT`

`core/settings.py` maps `ENVIRONMENT` to a module in `config/settings/`; the default is
`production`, and an unknown value raises `ValueError`.

- `development` — local dev: console email backend, `.ngrok-free.dev` hosts allowed, debug
  toolbar on by default (`DEBUG_TOOLBAR`, default `True` in
  `config/settings/development.py` — set `DEBUG_TOOLBAR=false` to opt out).
- `test` — `config/settings/local_test.py`, used by `make test`/`make cover`/`make check`:
  `TESTING=True`, in-memory email, allauth rate limits disabled, plain static storage (no
  `collectstatic` needed), a pool of 20 interchangeable test databases.
- `docker-devt` — same as development but for containers (DB/Redis hosts default to
  `postgres`/`redis`); debug toolbar opt-in only (`DEBUG_TOOLBAR`, default `False` in
  `config/settings/docker_devt.py`).
- `docker-test` — test settings inside the container (`make dtest`).
- `production` — requires `SECRET_KEY` and `SITE_DOMAIN`, SMTP email, strict WhiteNoise
  manifest.

## OAuth in development

Providers come from the `OAUTH_PROVIDERS` env var (`config/settings/base.py`); each provider
`<p>` needs `<P>_OAUTH_CLIENT_ID` and `<P>_OAUTH_CLIENT_SECRET` (plus `<P>_SERVER_URL` for
openid_connect providers such as PocketID). Without it, plain username/email + password login
works out of the box in development. See
[/specs/oauth-authentication.md](/specs/oauth-authentication.md) and the
[user manual OAuth page](https://cousins-matter.readthedocs.io/oauth-authentication/).

## Container entrypoint

`scripts/entrypoint.py` is what runs inside the app container: Redis leadership lock, `.env`
checks, first-run media dirs and `theme.css`, superuser creation from env vars, `migrate`,
`collectstatic`, `check --deploy`, then exec of the command. For operator-level installs
(`scripts/manage_cousins_matter.py install`, `migrate-v1-v2`, `rotate-secrets`), see the
[user manual installation page](https://cousins-matter.readthedocs.io/installation/).

# See also

- [Architecture](/architecture.md) — what each environment changes
- [Testing](/testing.md) — how to run the test suites
- [Conventions](/conventions.md)
- User manual: [installation](https://cousins-matter.readthedocs.io/installation/),
  [settings](https://cousins-matter.readthedocs.io/settings/)
