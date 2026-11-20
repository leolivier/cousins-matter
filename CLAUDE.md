# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cousins Matter is a self-hosted Django application for managing large families: member management, photo galleries, forums, chat rooms, polls, classified ads, genealogy (GEDCOM import/export), and a basic CMS.

## Standard Workflow
Verify before committing: run the `/ship` skill — it carries the full verify-then-commit checklist (make check/test/UI suite) and the multi-tenant QA gate.


## Communication
Always respond and write in English whatever the user is writing in (French or English) and never switch languages mid-session.

## Refactoring Conventions
Services-layer extraction pattern: keep views thin, move business logic into <app>/services.py, preserve existing return shapes, keep `ruff check` clean, and run that app's test suite before committing.

## Git & Environment
Never work directly on main: create a feature branch or git worktree before substantive changes. New worktrees are NOT broken — run `uv init && uv sync --dev && ln -s ../../../.env .env` in the worktree before using ruff, pyright, or pytest.
Activate the venv before running any commands: `source .venv/bin/activate`.
**Always** use the make commands — see the Makefile for the full list.

Test base class for auth/members: `members/tests/tests_member_base.py::MemberTestCase`.

## Architecture Notes (not obvious from the code)

- **Active settings** are picked by the `ENVIRONMENT` env var (default "production"): `config/settings/{base,development,production,local_test,docker_devt,docker_test}.py`.
- `manage.py` points to `core.settings` (non-standard module name).
- **Custom user model**: `members.models.Member` (extends AbstractUser) — always use `get_user_model()` or `Member`.
- **Feature flags**: `FEATURES_FLAGS` dict in settings, surfaced by `core.context_processors.features`.
- **Protected media** is served through `/protected_media/` with access control — never link media files directly; public media lives under `/media/public/`.
- **Async tasks** (emails, notifications) run via Django-Q2; `Q_SYNC=True` in dev executes them synchronously.
- **Followers**: members follow each other via `core.followers` utilities (drives notifications).
- **docs/ is an OKF bundle**: any PR touching an app or module must update its fiche in `docs/` (e.g. `members/` → `docs/apps/members.md`) and push that fiche's `stale_after` forward; `make check-docs` enforces frontmatter and lists stale fiches.
