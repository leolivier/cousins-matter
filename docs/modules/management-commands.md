---
type: Module Reference
title: Management Commands
description: Inventory of the project's manage.py commands (check_okf, generate_test_data, import_test_data, delete_tenant) and the scripts/manage_cousins_matter.py operations
tags: ["module", "management-commands"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T11:16:06Z }
---

# Management Commands

Only four `manage.py` commands are project code; everything else comes from
Django or dependencies. Remember to export the settings environment first
(`ENVIRONMENT=test SECRET_KEY=x POSTGRES_PASSWORD=x ./manage.py ...` locally
— see [Setup](/setup-dev.md#choosing-environment)).

## Project commands

| Command | Location | Purpose |
| --- | --- | --- |
| `check_okf [bundle]` | core/management/commands/check_okf.py | Check OKF v0.2 conformance of the docs bundle (frontmatter `type` + `stale_after` date); prints `ERROR`/`STALE` lines, exit 1 on errors. Wired as `make check-docs` (`ENVIRONMENT="test" ./manage.py check_okf docs`). |
| `generate_test_data [--app A] [--count N]` | core/management/commands/generate_test_data.py | Import `<app>/tests/factories.py` for every (or one) app, instantiate N objects per factory and dump fixtures into the app's `tests/resources/` folder. |
| `import_test_data [--app A]` | core/management/commands/import_test_data.py | `loaddata` each app's `tests/resources/fixtures.json` (apps visited in a fixed order because of FKs) to seed a dev/test database. |
| `delete_tenant <slug> [--yes]` | tenants/management/commands/delete_tenant.py | Hard-delete a tenant and all its data; refuses the system and currently-active tenants, and asks for confirmation unless `--yes`. |

Commands provided by dependencies that matter operationally: `qcluster`,
`qmonitor`, `qinfo` (django-q2 — the cluster that runs notifications), and
`captcha_clean` / `captcha_create_pool` (django-simple-captcha).

## scripts/manage_cousins_matter.py (host CLI, not manage.py)

Run inside the container/directory of a deployment; three subcommands:

- `install` — pre-flight checks (v1 directory leftovers, permissions),
  downloads a few files from GitHub, generates/rotates `SECRET_KEY` and the
  Postgres password if missing, creates directories with the right
  permissions, then opens an editor on `.env` after a countdown.
- `rotate-secrets` — rotates `SECRET_KEY` and appends the old one to
  `PREVIOUS_SECRET_KEYS` in `.env`.
- `migrate-v1-v2` — migrates a v1.x install to v2: checks, converts the
  sqlite3 database to Postgres, downloads v2 files from GitHub and rotates
  the secret key.

`scripts/entrypoint.py` is the container init (atomic first-run lock, wait
for DB, `migrate`, `collectstatic`, `check --deploy`, superuser creation
from env vars) — [Setup](/setup-dev.md#container-entrypoint) and
[Architecture](/architecture.md#docker-topology).

# See also

- [Core](/apps/core.md#management-commands) — the two test-data commands in
  their app context.
- [Testing](/testing.md) — how `generate_test_data`/`import_test_data` feed
  tests.
- User manual: <https://cousins-matter.readthedocs.io/other-management-operations/>.
