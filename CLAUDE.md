# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cousins Matter is a self-hosted Django application for managing large families: member management, photo galleries, forums, chat rooms, polls, classified ads, genealogy (GEDCOM import/export), and a basic CMS.

Stack: Django 6 + Channels (Daphne), PostgreSQL, Redis (cache + Django-Q2 tasks), Bulma/HTMX/crispy-forms, WhiteNoise, Docker Compose. Python 3.14+.

## Development and Test Commands

Activate the venv first: `source .venv/bin/activate` (provisioned by `uv sync`; a fresh git worktree has no `.venv` — run `uv init && uv sync --dev` there).

**Always** use the make commands — see the Makefile for the full list:

```bash
make up4run                # start postgres/redis/qcluster containers for local dev
make run                   # Django dev server on port 8000
make test t=<module>       # tests, e.g. make test t=members.tests.tests_member
make test-ui t=<module>    # Playwright UI tests
make cover                 # coverage report, 80% minimum enforced
make check                 # ruff format + ruff check + mypy — run before every commit
make mkmig / make mig      # create / apply migrations
make mkmsg a=<app> / make cpmsg a=<app>   # translations (en, fr, es, de, it, pt)
```

Test base class for auth/members: `members/tests/tests_member_base.py::MemberTestCase`.

## Architecture Notes (not obvious from the code)

- **Active settings** are picked by the `ENVIRONMENT` env var (default "production"): `config/settings/{base,development,production,local_test,docker_devt,docker_test}.py`.
- `manage.py` points to `core.settings` (non-standard module name).
- **Custom user model**: `members.models.Member` (extends AbstractUser) — always use `get_user_model()` or `Member`.
- **Feature flags**: `FEATURES_FLAGS` dict in settings, surfaced by `core.context_processors.features`.
- **Protected media** is served through `/protected_media/` with access control — never link media files directly; public media lives under `/media/public/`.
- **Async tasks** (emails, notifications) run via Django-Q2; `Q_SYNC=True` in dev executes them synchronously.
- **Followers**: members follow each other via `core.followers` utilities (drives notifications).
- **Services pattern**: business logic lives in `<app>/services.py`, extracted from views.
- Docker: `scripts/entrypoint.py` initializes containers; `scripts/manage_cousins_matter.py` is the install/management CLI; ASGI + Channels routing in `cousinsmatter/asgi.py`.
- **docs/ OKF bundle**: any PR touching an app or module must update its fiche (e.g. `docs/apps/members.md`) and run `make check-docs` (`manage.py check_okf docs` must stay green); list new fiches in `docs/index.md` and record notable changes in `docs/log.md`.
