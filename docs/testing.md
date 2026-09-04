---
type: Testing
title: Testing
description: Run the Django, Playwright UI and coverage suites, and the pre-commit quality gate
tags: [testing, playwright, coverage]
status: draft
stale_after: 2027-03-04
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T12:00:00Z }
---

# Testing

## Unit / integration tests

```bash
make test t=<module>    # ENVIRONMENT="test" ./manage.py test --exclude-tag=ui <module>
```

(`Makefile`) The `ui` tag is excluded, so plain `make test` never boots a browser. A module
path looks like `members.tests.tests_member`. Tests need PostgreSQL and Redis reachable —
start them with `make up4run` (see [Development Setup](/setup-dev.md)).

## UI tests (Playwright)

```bash
make test-ui t=<module>   # ENVIRONMENT="test" ./manage.py test --tag=ui <module>
```

UI tests are Django tests tagged `ui` and live in `<app>/tests/ui/` — present for `chat`,
`classified_ads`, `core`, `forum`, `galleries`, `genealogy`, `members`, `polls` and `troves`.
They use `playwright` (dev group in `pyproject.toml`) on top of
`StaticLiveServerTestCase`; `config/settings/local_test.py` switches static files to plain
`StaticFilesStorage` so live-server pages resolve without `collectstatic`.

## Test base class

Tests touching members/auth extend `MemberTestCase` from
`members/tests/tests_member_base.py` (class `MemberTestCase`, built on
`MemberTestCaseMixin` + `TestCase`), which sets up a family and member fixtures.

## Test-environment specifics worth knowing

From `config/settings/local_test.py` (and `docker_test.py` for the container variant):

- `EMAIL_BACKEND` is in-memory (`locmem`), so sent mails are assertable.
- `ACCOUNT_RATE_LIMITS = False` — the allauth login rate limit is disabled because the UI
  suite performs ~190 logins from localhost.
- Test DBs are named `test_cousinsmatter_<0-20>` to allow parallel runs, and the psycopg pool
  option is removed.

## Coverage

```bash
make cover                       # all apps, report to .coverage
make cover a=<app>               # one app, data file .coverage.<app>
make cover co=... to=...         # extra coverage / test options
```

`make cover` runs `coverage run --source=... ./manage.py test` then
`coverage report --fail-under=80` with the `EXCLUDE_COVER` omit list (`Makefile`):
settings, scripts, migrations, tests and a few wrappers are excluded. The 80% minimum is
enforced by the `--fail-under` flag.

## Quality gate: `make check`

`make check` (see `Makefile`) runs, in order:

1. `ruff format -q .`
2. `ruff check . --fix`
3. `mypy ./ --ignore-missing-imports --exclude migrations/* --exclude .venv/*`
4. `bandit -r . -c pyproject.toml -f txt -o bandit.out`
5. `pip-audit .`
6. `ENVIRONMENT="test" ./manage.py check_okf docs` (same as `make check-docs`, which checks
   the OKF frontmatter of this bundle)

Run it before every commit.

# See also

- [Development Setup](/setup-dev.md) — services needed by the tests
- [Architecture](/architecture.md) — the `test` settings module
- [Conventions](/conventions.md)
