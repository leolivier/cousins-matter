# OKF Repo Documentation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create in `docs/` an OKF v0.2 bundle documenting the repo for developers and AI agents (spec: `docs/superpowers/specs/2026-09-04-okf-repo-docs-design.md`).

**Architecture:** `docs/` is one OKF bundle: transverse fiches at the root, then `apps/` (one per Django app), `modules/` (cross-cutting concerns), `flows/` (end-to-end business flows), `specs/` (dev-level feature specs), `plan/` (roadmap + debt), plus reserved `index.md` and `log.md`. Conformance is enforced by a Django management command `manage.py check_okf` wired into `make check`.

**Tech Stack:** Django management command (stdlib only), YAML frontmatter per OKF v0.2, Django TestCase for the check's unit test, Makefile target.

## Global Constraints

- **OKF spec v0.2** (https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md): every non-reserved `.md` has YAML frontmatter with non-empty `type`; reserved files are `index.md` and `log.md`; `log.md` has date-titled entries, newest first; internal links are bundle-root-relative (`[members](/apps/members.md)`); actors in `generated.by` use `<producer>/<version>`.
- **Excluded from the check:** `docs/superpowers/` (superpowers design/plan docs, no OKF frontmatter) and `log.md` (reserved).
- **Frontmatter template — copy verbatim, replace `<placeholders>`:**

```markdown
---
type: <TYPE>
title: <Title>
description: <one line, imperative-ish, no trailing period>
tags: [<tag1>, <tag2>]
status: draft
stale_after: 2027-03-04
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T12:00:00Z }
---
```

- `stale_after` = writing date + 6 months (all fiches written 2026-09-04 → `2027-03-04`). `status: draft` everywhere (no human review yet).
- **Fiche body rules:** English; every factual claim derived from code actually read in the listed sources; cite real paths (`members/models.py`, `<app>/services.py`) inline; end with a `# See also` section of bundle-root-relative links + user-manual page links where one exists; never duplicate user-manual content (link to it).
- **Type vocabulary:** `Architecture`, `Conventions`, `Setup`, `Testing`, `App Reference`, `Module Reference`, `Flow`, `Feature Spec`, `Plan`, `Directory`.
- **Local apps** (`config/settings/base.py` `LOCAL_APPS`): core, tenants, members, chat, galleries, classified_ads, cousinsmatter, forum, genealogy, pages, polls, troves. `cousinsmatter` is the project module (settings/ASGI) — covered by `architecture.md`, no app fiche.
- **Commits:** conventional-commit messages ending with `Co-Authored-By: Claude Code <noreply@anthropic.com>`.
- **Branch:** work in the `worktree-okf-docs` worktree (already checked out).

---

### Task 1: OKF conformance check (`manage.py check_okf`)

**Files:**
- Test: `core/tests/test_check_okf.py`
- Create: `core/management/commands/check_okf.py`
- Modify: `Makefile` (after line 102, the end of the `check:` recipe, add a line; add new target near `test:`)

**Interfaces:**
- Produces: `check_bundle(bundle: Path) -> tuple[list[str], list[str]]` in `core/management/commands/check_okf.py` — returns `(errors, stale)`; `errors` non-empty ⇒ exit 1. Makefile targets `check-docs` (runs the command on `docs`) and `check` (runs `check-docs` at the end).

- [ ] **Step 1: Write the failing test**

Create `core/tests/test_check_okf.py`:

```python
import tempfile
from datetime import date, timedelta
from pathlib import Path

from django.test import SimpleTestCase

from core.management.commands.check_okf import check_bundle


def _write(base: Path, rel: str, text: str) -> None:
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class CheckBundleTests(SimpleTestCase):
    def _bundle(self, **files: str) -> Path:
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        b = Path(d.name)
        for name, text in files.items():
            _write(b, name, text)
        return b

    def test_conformant_bundle_passes(self) -> None:
        b = self._bundle(
            **{
                "index.md": "---\ntype: Directory\ntitle: Index\n---\n\n# Index\n",
                "apps/members.md": "---\ntype: App Reference\ntitle: Members\n---\n\n# Members\n",
            }
        )
        self.assertEqual(check_bundle(b), ([], []))

    def test_missing_frontmatter_fails(self) -> None:
        errors, stale = check_bundle(self._bundle(**{"bad.md": "# no frontmatter\n"}))
        self.assertEqual(errors, ["bad.md: missing frontmatter"])
        self.assertEqual(stale, [])

    def test_empty_type_fails(self) -> None:
        errors, _ = check_bundle(self._bundle(**{"a.md": "---\ntitle: X\n---\n\n# X\n"}))
        self.assertEqual(errors, ["a.md: empty `type`"])

    def test_reserved_and_superpowers_excluded(self) -> None:
        b = self._bundle(
            **{
                "log.md": "# Log\n\n## 2026-09-04\n- init\n",
                "superpowers/spec.md": "# spec\n",
                "index.md": "---\ntype: Directory\n---\n",
            }
        )
        self.assertEqual(check_bundle(b), ([], []))

    def test_stale_listed_but_not_failing(self) -> None:
        past = (date.today() - timedelta(days=1)).isoformat()
        errors, stale = check_bundle(
            self._bundle(**{"plan/roadmap.md": f"---\ntype: Plan\nstale_after: {past}\n---\n\n# Roadmap\n"})
        )
        self.assertEqual(errors, [])
        self.assertEqual(stale, [f"plan/roadmap.md: stale since {past}"])

    def test_bad_stale_after_fails(self) -> None:
        errors, stale = check_bundle(
            self._bundle(**{"a.md": "---\ntype: Plan\nstale_after: not-a-date\n---\n\n# A\n"})
        )
        self.assertEqual(errors, ["a.md: bad `stale_after` (want ISO date)"])
        self.assertEqual(stale, [])
```

- [ ] **Step 2: Run the test, verify it fails with ImportError**

Run: `make test t=core.tests.test_check_okf`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.management.commands.check_okf'`

- [ ] **Step 3: Write the minimal implementation**

Create `core/management/commands/check_okf.py`:

```python
"""Check OKF v0.2 conformance of a documentation bundle (default: docs/).

Every non-resorted ``.md`` file must have a YAML frontmatter with a non-empty
``type``. ``log.md`` and ``docs/superpowers/`` are excluded. Files whose
``stale_after`` date has passed are listed as warnings (not errors).
"""
import re
from datetime import date
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

RESERVED = {"log.md"}
EXCLUDED_DIRS = {"superpowers"}
FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def frontmatter(text: str) -> str | None:
    m = FM_RE.match(text)
    return m.group(1) if m else None


def field(fm: str, name: str) -> str | None:
    m = re.search(rf"^{name}:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip() if m else None


def check_bundle(bundle: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    stale: list[str] = []
    for md in sorted(bundle.rglob("*.md")):
        rel = md.relative_to(bundle)
        if md.name in RESERVED or rel.parts[0] in EXCLUDED_DIRS:
            continue
        fm = frontmatter(md.read_text(encoding="utf-8"))
        if fm is None:
            errors.append(f"{rel}: missing frontmatter")
            continue
        if not field(fm, "type"):
            errors.append(f"{rel}: empty `type`")
        sa = field(fm, "stale_after")
        if sa:
            try:
                if date.fromisoformat(sa[:10]) < date.today():
                    stale.append(f"{rel}: stale since {sa[:10]}")
            except ValueError:
                errors.append(f"{rel}: bad `stale_after` (want ISO date)")
    return errors, stale


class Command(BaseCommand):
    help = "Check OKF v0.2 conformance of the docs/ bundle"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("bundle", nargs="?", default="docs", type=str)

    def handle(self, *args: str, **options: Any) -> None:
        errors, stale = check_bundle(Path(str(options["bundle"])))
        for e in errors:
            self.stdout.write(self.style.ERROR(f"ERROR {e}"))
        for s in stale:
            self.stdout.write(self.style.WARNING(f"STALE  {s}"))
        if errors:
            raise SystemExit(1)
```

- [ ] **Step 4: Run the test, verify it passes**

Run: `make test t=core.tests.test_check_okf`
Expected: OK (6 tests)

- [ ] **Step 5: Wire into the Makefile**

In `Makefile`, inside the `check:` recipe (after the `pip-audit .` line, same tab indentation), add:

```make
	ENVIRONMENT="test" ./manage.py check_okf docs
```

After the `test:` target, add:

```make
check-docs:
	ENVIRONMENT="test" ./manage.py check_okf docs
```

- [ ] **Step 6: Run both targets**

Run: `make check-docs`
Expected: exit 0, no output (docs/ has no non-excluded fiches yet).

- [ ] **Step 7: Commit**

```bash
git add core/management/commands/check_okf.py core/tests/test_check_okf.py Makefile
git commit -m "feat(docs): add OKF conformance check (manage.py check_okf)

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 2: Root transverse fiches (architecture, conventions, setup-dev, testing)

**Files:**
- Create: `docs/architecture.md`, `docs/conventions.md`, `docs/setup-dev.md`, `docs/testing.md`

**Interfaces:**
- Consumes: `check_bundle` from Task 1 (via `make check-docs`).
- Produces: bundle-root-relative link targets `/architecture.md`, `/conventions.md`, `/setup-dev.md`, `/testing.md` used by later tasks.

Fiche frontmatter values (copy the template, then):

| file | type | title | tags |
|---|---|---|---|
| `docs/architecture.md` | `Architecture` | Architecture | `[architecture, settings, asgi, docker]` |
| `docs/conventions.md` | `Conventions` | Conventions | `[conventions, services, followers, feature-flags, i18n]` |
| `docs/setup-dev.md` | `Setup` | Development Setup | `[setup, makefile, uv, docker]` |
| `docs/testing.md` | `Testing` | Testing | `[testing, playwright, coverage]` |

**Sources to read before writing:** `CLAUDE.md` (repo root), `config/settings/base.py` (+ list `config/settings/`), `cousinsmatter/asgi.py`, `cousinsmatter/urls.py`, `Makefile`, `manage.py`, `scripts/entrypoint.py`, `scripts/manage_cousins_matter.py`, `pyproject.toml`, `docker-compose.yml`.

**Must cover:**
- `architecture.md`: settings selection via `ENVIRONMENT` (`config/settings/{base,development,production,local_test,docker_devt,docker_test}.py`); `manage.py` points at `core.settings`; middleware order (TenantMiddleware, LoginRequiredMiddleware, WhiteNoise, CSP, allauth, htmx); ASGI + Channels (`cousinsmatter/asgi.py`); WhiteNoise for static; protected media served through `/protected_media/` with access control, public media under `/media/public/`; Docker compose services (postgres, redis, qcluster); multi-tenancy pointer to `/specs/multi-tenancy.md`.
- `conventions.md`: services pattern (business logic in `<app>/services.py` or `services/`); custom user model `members.models.Member` + always `get_user_model()`; followers utilities in `core.followers` driving notifications; `FEATURES_FLAGS` dict surfaced by `core.context_processors.features`; async via Django-Q2 with `Q_SYNC=True` in dev; translations workflow (`make mkmsg`/`make cpmsg`, 6 locales); themes/customization pointer to `/modules/themes.md`.
- `setup-dev.md`: `uv sync --dev` + `.venv/bin/activate`; `make up4run` (postgres/redis/qcluster), `make run` (port 8000), `make mkmig`/`make mig`, `make mkmsg a=<app>`/`make cpmsg a=<app>`; `ENVIRONMENT` values and when to use each; OAuth/local test settings.
- `testing.md`: `make test t=<module>` (excludes `--tag=ui`), `make test-ui t=<module>`; base class `members/tests/tests_member_base.py::MemberTestCase`; coverage `make cover`, 80% minimum enforced; `make check` = ruff format + ruff check + mypy + bandit + pip-audit + `check-docs`; UI tests live in `<app>/tests/ui/` (Playwright).

Each fiche ends with `# See also` linking to the others and to relevant user-manual pages (`user-manual/installation.md`, `user-manual/settings.md`, `user-manual/translations.md` on readthedocs).

- [ ] **Step 1: Read the sources listed above**
- [ ] **Step 2: Write the four fiches** (frontmatter from the table, body per must-cover)
- [ ] **Step 3: Verify conformance**

Run: `make check-docs`
Expected: exit 0

- [ ] **Step 4: Commit**

```bash
git add docs/architecture.md docs/conventions.md docs/setup-dev.md docs/testing.md
git commit -m "docs(okf): root transverse fiches (architecture, conventions, setup-dev, testing)

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 3: apps/ fiches — members, core, tenants

**Files:**
- Create: `docs/apps/members.md`, `docs/apps/core.md`, `docs/apps/tenants.md`

**Interfaces:**
- Produces: link targets `/apps/members.md`, `/apps/core.md`, `/apps/tenants.md`.

Fiche frontmatter values: all `type: App Reference`, titles `Members`, `Core`, `Tenants`, tags `["app", "<app-name>"]`.

**Sources to read:** `members/models.py`, `members/managers.py`, `members/views/`, `members/services/`, `members/registration_link_manager.py`, `members/tasks.py`, `members/adapter.py`, `members/urls.py`; `core/models.py`, `core/views/`, `core/services.py`, `core/followers.py` (verify actual filename with `ls core/`), `core/tasks_schedules.py`, `core/context_processors.py`, `core/middleware.py`; `tenants/models.py`, `tenants/middleware.py`, `tenants/services.py`, `tenants/views.py` (verify with `ls tenants/`).

**Must cover:**
- `members.md`: `Member` (AbstractUser, AUTH_USER_MODEL), managed members, invitations, registration links, bulk import, following; per-family role/permissions; user-manual cross-link.
- `core.md`: site-wide models (pages of general utility, contact form, featured, stats), followers, notification batching, protected media views, context processors, management commands (`generate_test_data`, `import_test_data`).
- `tenants.md`: `Family` model, shared-schema isolation, `TenantMiddleware`, RLS hardening, `MULTI_TENANT_ENABLED` setting; pointer to `/specs/multi-tenancy.md`.

- [ ] **Step 1: Read the sources, verify file names by listing each app dir**
- [ ] **Step 2: Write the three fiches** (frontmatter from above, body per must-cover, `# See also` linking to `/specs/multi-tenancy.md`, `/modules/followers.md` where relevant)
- [ ] **Step 3:** Run `make check-docs` — expected: exit 0
- [ ] **Step 4: Commit**

```bash
git add docs/apps/members.md docs/apps/core.md docs/apps/tenants.md
git commit -m "docs(okf): app fiches — members, core, tenants

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 4: apps/ fiches — galleries, forum, chat

**Files:**
- Create: `docs/apps/galleries.md`, `docs/apps/forum.md`, `docs/apps/chat.md`

Fiche frontmatter values: `type: App Reference`, titles `Galleries`, `Forum`, `Chat`, tags `["app", "<app-name>"]`.

**Sources to read:** `galleries/models.py`, `galleries/views.py`, `galleries/services.py`, `galleries/urls.py`; `forum/models.py`, `forum/views.py`, `forum/services.py`; `chat/models.py`, `chat/consumers.py`, `chat/services.py`, `chat/routing.py` (verify names by listing each dir).

**Must cover:**
- `galleries.md`: gallery tree model, bulk photo import, protected storage of photos, thumbnails.
- `forum.md`: posts/answers models, notifications on new posts (via followers), subscription model.
- `chat.md`: public/private rooms, Channels consumers, routing, chat notifications.

- [ ] **Step 1: Read the sources**
- [ ] **Step 2: Write the three fiches** (`# See also`: `/modules/notifications.md`, `/modules/protected-media.md` where relevant)
- [ ] **Step 3:** Run `make check-docs` — expected: exit 0
- [ ] **Step 4: Commit**

```bash
git add docs/apps/galleries.md docs/apps/forum.md docs/apps/chat.md
git commit -m "docs(okf): app fiches — galleries, forum, chat

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 5: apps/ fiches — polls, classified-ads, pages

**Files:**
- Create: `docs/apps/polls.md`, `docs/apps/classified-ads.md`, `docs/apps/pages.md`

Fiche frontmatter values: `type: App Reference`, titles `Polls`, `Classified Ads`, `Pages`, tags `["app", "<app-name>"]`. Note: file names use hyphens (`classified-ads.md`), Django app labels keep underscores (`classified_ads`) — mention both in each fiche's frontmatter `description`.

**Sources to read:** `polls/models.py`, `polls/views.py`, `polls/services.py`; `classified_ads/models.py`, `classified_ads/views.py`, `classified_ads/services.py`; `pages/models.py`, `pages/views.py`.

**Must cover:**
- `polls.md`: poll models incl. event-planning survey submodule (scheduling); who can create/answer.
- `classified-ads.md`: ad model, moderation/publication rules, known N+1 analysis pointer to `/plan/debt.md`.
- `pages.md`: basic CMS, admin publication workflow.

- [ ] **Step 1: Read the sources**
- [ ] **Step 2: Write the three fiches**
- [ ] **Step 3:** Run `make check-docs` — expected: exit 0
- [ ] **Step 4: Commit**

```bash
git add docs/apps/polls.md docs/apps/classified-ads.md docs/apps/pages.md
git commit -m "docs(okf): app fiches — polls, classified-ads, pages

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 6: apps/ fiches — troves, genealogy

**Files:**
- Create: `docs/apps/troves.md`, `docs/apps/genealogy.md`

Fiche frontmatter values: `type: App Reference`, titles `Troves`, `Genealogy`, tags `["app", "<app-name>"]`.

**Sources to read:** `troves/models.py`, `troves/views.py`; `genealogy/models.py`, `genealogy/views.py`, `genealogy/services.py`, plus GEDCOM import/export modules (find with `grep -ril gedcom genealogy/ | head -20`).

**Must cover:**
- `troves.md`: family numeric treasures (texts, music, videos), publication rules.
- `genealogy.md`: family-tree models, GEDCOM import and export flows, link to `/flows/gedcom-import-export.md`.

- [ ] **Step 1: Read the sources**
- [ ] **Step 2: Write the two fiches**
- [ ] **Step 3:** Run `make check-docs` — expected: exit 0
- [ ] **Step 4: Commit**

```bash
git add docs/apps/troves.md docs/apps/genealogy.md
git commit -m "docs(okf): app fiches — troves, genealogy

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 7: modules/ fiches (6)

**Files:**
- Create: `docs/modules/followers.md`, `docs/modules/notifications.md`, `docs/modules/protected-media.md`, `docs/modules/feature-flags.md`, `docs/modules/themes.md`, `docs/modules/management-commands.md`

Fiche frontmatter values: all `type: Module Reference`, titles `Followers`, `Notifications`, `Protected Media`, `Feature Flags`, `Themes & Customization`, `Management Commands`, tags `["module", "<topic>"]`.

**Sources to read:** `core/followers.py` (verify name), `core/tasks.py` / `core/tasks_schedules.py`, notification modules per app (`grep -rl notification --include=*.py | head -20`), `core/views/protected_media.py` or equivalent (`grep -r "protected_media" core/ config/ | head`), `FEATURES_FLAGS` in `config/settings/base.py` + `core/context_processors.py`, theme/static files under `core/static/` and customization views (`grep -rl theme core/ members/ | head`), all commands under `*/management/commands/`.

**Must cover:**
- `followers.md`: follow/unfollow utilities, what follows trigger.
- `notifications.md`: Django-Q2 async tasks, batching, `Q_SYNC` behaviour in dev, per-app notification kinds.
- `protected-media.md`: URL prefix, access-control view, settings; public media contrast.
- `feature-flags.md`: `FEATURES_FLAGS` keys, per-family/per-site surfacing, how to add a flag.
- `themes.md`: admin customization and theming, CSS assets, user-manual cross-link (`customizing` page).
- `management-commands.md`: inventory of every command in `*/management/commands/` with one-line purpose (including `check_okf` from Task 1 and `scripts/manage_cousins_matter.py` operations).

- [ ] **Step 1: Read the sources (verify every path you cite)**
- [ ] **Step 2: Write the six fiches**
- [ ] **Step 3:** Run `make check-docs` — expected: exit 0
- [ ] **Step 4: Commit**

```bash
git add docs/modules/
git commit -m "docs(okf): module fiches (followers, notifications, protected-media, flags, themes, commands)

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 8: flows/ fiches (4)

**Files:**
- Create: `docs/flows/member-invitation.md`, `docs/flows/gedcom-import-export.md`, `docs/flows/gallery-bulk-import.md`, `docs/flows/oauth-login.md`

Fiche frontmatter values: all `type: Flow`, titles `Member Invitation`, `GEDCOM Import/Export`, `Gallery Bulk Import`, `OAuth Login`, tags `["flow", "<topic>"]`.

**Sources to read (trace the actual code path end to end):** `members/views/registration*` or invitation views, `members/registration_link_manager.py`, `members/forms.py`; `genealogy/services.py` + GEDCOM modules; `galleries/views.py` bulk import path; `members/adapter.py`, allauth settings in `config/settings/base.py`, `cousinsmatter/urls.py`.

**Must cover (same shape for each flow):** numbered steps from entry point to end state, the exact functions/views involved (`path: symbol`), side effects (emails, notifications, DB writes), failure modes visible to the user.

- [ ] **Step 1: Read and trace the sources**
- [ ] **Step 2: Write the four fiches**
- [ ] **Step 3:** Run `make check-docs` — expected: exit 0
- [ ] **Step 4: Commit**

```bash
git add docs/flows/
git commit -m "docs(okf): flow fiches (invitation, gedcom, gallery import, oauth)

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 9: specs/ fiches (3)

**Files:**
- Create: `docs/specs/multi-tenancy.md`, `docs/specs/oauth-authentication.md`, `docs/specs/media-storage.md`

Fiche frontmatter values: all `type: Feature Spec`, titles `Multi-Tenancy`, `OAuth Authentication`, `Media Storage`, tags `["spec", "<topic>"]`.

**Sources to read:** `tenants/` (all), migration files under `tenants/migrations/` for the RLS/isolation story, `config/settings/base.py` tenancy + allauth + media settings, `user-manual/multi-tenancy.md`, `user-manual/oauth-authentication.md`, `user-manual/media-storage.md`, `user-manual/media-storage-with-dropbox.md`.

**Must cover:** dev-level behaviour and invariants (what the user-manual pages don't say): schema/isolation model, RLS enforcement points, Dropbox option, per-tenant settings; explicitly link the corresponding user-manual pages instead of restating them.

- [ ] **Step 1: Read the sources**
- [ ] **Step 2: Write the three fiches**
- [ ] **Step 3:** Run `make check-docs` — expected: exit 0
- [ ] **Step 4: Commit**

```bash
git add docs/specs/
git commit -m "docs(okf): feature specs — multi-tenancy, oauth, media-storage

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 10: plan/ fiches (2)

**Files:**
- Create: `docs/plan/roadmap.md`, `docs/plan/debt.md`

Fiche frontmatter values: `type: Plan`, titles `Roadmap`, `Known Debt`, tags `["plan"]` / `["plan", "debt"]`. For these two only, set `stale_after: 2026-12-04` (plans rot faster than reference docs).

**Sources to read:** `classified_ads_n+1_analysis.md` (repo root — move its findings in, keep the file), open GitHub issues (`gh issue list --limit 30`), `release.txt`.

**Must cover:**
- `roadmap.md`: in-flight and planned work derived from open issues + recent commits (multi-tenancy follow-ups).
- `debt.md`: known shortcuts: classified_ads N+1 findings (from the root analysis file), any `ponytail:` comments (`grep -rn "ponytail:" --include=*.py . | head -20`), TODO/FIXME hotspots (`grep -rn "TODO\|FIXME" --include=*.py . | wc -l` and top files).

- [ ] **Step 1: Read sources, run the greps**
- [ ] **Step 2: Write the two fiches**
- [ ] **Step 3:** Run `make check-docs` — expected: exit 0, with `STALE` warnings only for files whose `stale_after` is in the past (none at this point)
- [ ] **Step 4: Commit**

```bash
git add docs/plan/
git commit -m "docs(okf): plan fiches — roadmap and known debt

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 11: index.md, log.md, maintenance rule in CLAUDE.md

**Files:**
- Create: `docs/index.md`, `docs/log.md`
- Modify: `CLAUDE.md` (repo root, project instructions section)

**Interfaces:**
- Produces: `/index.md` — the directory every agent reads first; `log.md` — the bundle history.

- [ ] **Step 1: Write `docs/index.md`**

Frontmatter: `type: Directory`, `title: Cousins Matter Knowledge Bundle`, `description: OKF bundle documenting the repo for developers and AI agents`, `tags: [index]`. Body: one section per subdirectory (`Architecture & conventions`, `Apps`, `Modules`, `Flows`, `Specs`, `Plans`) each a bulleted list of `[Title](/<path>.md)` links to **every** fiche created in Tasks 2–10, plus links to `log.md` and to the user-manual (readthedocs URL from `mkdocs.yml`). Start the body with a 3-line bundle orientation: what this bundle is, OKF v0.2, status all `draft`.

- [ ] **Step 2: Write `docs/log.md`** (no frontmatter — reserved file, newest first)

```markdown
# Log

## 2026-09-04

- Created the OKF bundle: root fiches (architecture, conventions, setup-dev, testing), 11 app fiches, 6 module fiches, 4 flow fiches, 3 feature specs, plan/roadmap + plan/debt, and the `manage.py check_okf` conformance check wired into `make check`.
- All fiches `status: draft`, `stale_after: 2027-03-04` (plan/ fiches: 2026-12-04).
```

- [ ] **Step 3: Add the maintenance rule to `CLAUDE.md`** — under the Architecture Notes section, add:

```markdown
- **docs/ is an OKF bundle**: any PR touching an app or module must update its fiche in `docs/` (e.g. `members/` → `docs/apps/members.md`) and push that fiche's `stale_after` forward; `make check-docs` enforces frontmatter and lists stale fiches.
```

- [ ] **Step 4:** Run `make check-docs` — expected: exit 0
- [ ] **Step 5: Commit**

```bash
git add docs/index.md docs/log.md CLAUDE.md
git commit -m "docs(okf): bundle index, log, and CLAUDE.md maintenance rule

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 12: Final verification

- [ ] **Step 1:** Run `make check-docs` — expected: exit 0, no ERROR, no STALE.
- [ ] **Step 2:** Run `make test t=core.tests.test_check_okf` — expected: OK (6 tests).
- [ ] **Step 3:** Run `make check` — expected: ruff, ruff format, mypy, bandit, pip-audit and check-docs all pass.
- [ ] **Step 4:** Spot-check 3 random fiches: every cited path exists (`ls <path>`), links resolve (`docs/<linked path>` exists), frontmatter matches the template.
- [ ] **Step 5:** No commit unless something was fixed in steps 1–4; if fixes were made, commit them with the same conventions.

---

## Self-Review

- **Spec coverage:** §2 arborescence → Tasks 2–11 (backup.md dropped — no `backup` app exists in `LOCAL_APPS`, corrected from the original design tree); §3 frontmatter → Global Constraints + Task 1 check; §4 content rules → Global Constraints + per-task must-cover; §5 garde-fou → Task 1; §6 production → task ordering, sources per task; §7 maintien à jour → `stale_after` in template, Task 11 Step 3 (CLAUDE.md rule), Task 10 (fresher `stale_after` for plan fiches), `check-docs` stale listing (Task 1).
- **Placeholder scan:** no TBD/TODO; every task has exact paths, frontmatter values, commands and expected output.
- **Type consistency:** `check_bundle(bundle: Path) -> tuple[list[str], list[str]]` used in Task 1 (definition) and Task 1 test; `check-docs` target name consistent across Makefile, Tasks 2–12; fiche paths in `index.md` (Task 11) match the Create paths of Tasks 2–10.
