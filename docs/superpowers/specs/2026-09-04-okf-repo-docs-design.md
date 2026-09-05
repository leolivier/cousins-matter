# Design — Repo Documentation in OKF Format

- **Date**: 2026-09-04
- **Status**: Approved by the user (design presented during the session; Section 7 added at the user’s request)
- **Reference Spec**: [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) (GoogleCloudPlatform/knowledge-catalog)

## 1. Objective

Create, in `docs/`, an OKF v0.2 bundle documenting the Cousins Matter repository for
**developers and AI agents**. Each `.md` file in the bundle includes YAML frontmatter
where the only field required by the spec is `type`. A single bundle
(approach A selected; alternatives B “multi-bundles” and C “flat” rejected).

The bundle does not duplicate the existing user manual (`user-manual/`, MkDocs
on ReadTheDocs): it references it.

## 2. Directory Structure (~34 files)

```
docs/
  index.md              # directory: links to all documentation pages
  log.md                # chronological history (most recent first)
  architecture.md       # settings/ENVIRONMENT, ASGI+Channels, Docker, WhiteNoise
  conventions.md        # services pattern, followers, feature flags, i18n, Q_SYNC
  setup-dev.md          # uv, make up4run/run/test/cover/check, ENVIRONMENT
  testing.md            # MemberTestCase, Playwright UI tests, 80% coverage
  apps/                 # 12 files, one per Django app
    members.md core.md tenants.md galleries.md forum.md chat.md
    polls.md classified-ads.md pages.md troves.md genealogy.md backup.md
  modules/              # 6 files, one per module
    followers.md notifications.md protected-media.md
    feature-flags.md themes.md management-commands.md
  flows/                # 4 files, one per flow
    member-invitation.md gedcom-import-export.md
    gallery-bulk-import.md oauth-login.md
  specs/                # 3 technical specs (dev level)
    multi-tenancy.md oauth-authentication.md media-storage.md
  plan/
    roadmap.md          # work in progress / to do
    debt.md             # known shortcuts (dont classified_ads_n+1_analysis.md)
  superpowers/          # outside bundle OKF (see §5), superpowers design specs
```

## 3. Common Frontmatter

**Required** field (spec §2): `type`.

Bundle `type` vocabulary: `Architecture`, `Conventions`, `Setup`,
`Testing`, `App Reference`, `Module Reference`, `Flow`, `Feature Spec`,
`Plan`, `Directory`.

**Recommended** fields that must always be filled in: `title`, `description`,
`tags` (YAML list).

Special cases for reserved files (spec §8-9): `index.md` has frontmatter
`type: Directory` (consistent, verified by the check); `log.md` has no
frontmatter—the check excludes it like other reserved files, as its
structure is dictated by the spec.

Lifecycle: `status: draft` until the file is reviewed by a human;
`stale_after` set to +6 months (see §7). `generated: {by: claude-code,
at: <ISO 8601 Z>}` on every creation **and** rewrite. `verified` left blank
(OKF trusted services: *unverified* by default, *human-reviewed* later).

Internal links relative to the bundle root: `[members](/apps/members.md)`.

## 4. Content of the documentation files

- Each documentation file lists the key files and symbols along with their paths
  (`members/models.py`, `<app>/services.py`…).
- Final section `# See also`: cross-references to related apps, modules, and flows, and
  to pages in the user manual when they exist.
- `index.md` lists all documentation pages by subfolder; `log.md` follows the format
  specified by the spec (date titles `YYYY-MM-DD`, most recent first).
- The documentation pages are based on actual code (collected via codegraph/readings), not
  on session history.

## 5. Compliance Guardrails

`make check-docs`: a Python script (~15 lines, stdlib only) that verifies
that every non-reserved `.md` file in `docs/` has YAML frontmatter that can be parsed with a
non-empty `type`, that `index.md`/`log.md` are not reused as documentation files,
that `stale_after` (if present) is a date, and **lists the outdated documentation files**.
OKF compliance boils down to these rules (spec §11); no other
tools are required. The check excludes `docs/superpowers/` (superpowers design specs,
OKF frontmatter not applicable). Target added to the existing `check`.

## 6. Production

Fact gathering per app (codegraph + targeted readings), drafting one page at a
time, `log.md` kept up to date as work progresses. Details (breakdown, parallelization,
order) in the implementation plan written by the `writing-plans` skill.

## 7. Keeping Records Up to Date

- **`stale_after` on each record**: ISO date after which the record
  is considered suspect (default: +6 months); `make check-docs` lists expired records.
- **`generated: {by, at}` updated with each rewrite**: the actual age of
  each entry can be found in its frontmatter.
- **Workflow rule** (2 lines in `CLAUDE.md`): any PR that modifies an
  app updates its entry (`members/` → `docs/apps/members.md`) and advances its
  `stale_after`, as specified in the migration.
- **`log.md`**: an entry dated by each substantial update.
- **Release milestone**: For each tag, process the
  outdated documentation pages—integrated into the existing release process, no dedicated CI.

## 8. Out of Scope

- Bundle translation (i18n)—the bundle is in English, as are the code and user manual.
- Automatic generation of documentation files via CI or a periodic task.
- Migration of `user-manual/` content (these remain the user reference).
