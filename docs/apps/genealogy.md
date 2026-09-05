---
type: App Reference
title: Genealogy
description: Genealogy app (`genealogy`) — family-tree models (Person/Family), interactive family chart, statistics, and GEDCOM 5.5.1 import/export; documented in apps/genealogy.md
tags: ["app", "genealogy"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-04T22:53:05Z }
---

# Genealogy

`genealogy` keeps the family tree: `Person` and `Family` (unions)
records, an interactive family chart, a statistics page, and — the
front door for real data — GEDCOM 5.5.1 import/export. Business logic
lives in genealogy/services.py and genealogy/utils.py; the views in
genealogy/views/ are thin wrappers. The step-by-step GEDCOM round trip
is described in [the GEDCOM flow](/flows/gedcom-import-export.md); this
fiche stops at the moving parts.

**Tenant note:** `Person` and `Family` inherit `models.Model` directly —
**not** [TenantModel](/apps/tenants.md)-scoped. Tree data is shared
platform-wide, like [troves](/apps/troves.md) and
[forum](/apps/forum.md). One tenant knob does exist: the chart root
person is read through `tenant_setting("family_chart_root_person_id")`
(tenants/settings_overrides.py), so each family can point its chart at
a different ancestor even though the records themselves are shared.

## Models (genealogy/models.py)

- `Person` — `first_name`/`last_name`, `sex` (M/F/O, default O),
  birth and death `DateField` + place, `notes`, and the bookkeeping:
  - `member` — nullable OneToOne to `Member`
    (`related_name="genealogy_person"`): links a tree person to a real
    account;
  - `gedcom_id` — the GEDCOM pointer (`@I12@`), unique when set; this
    is the import/export identity;
  - `uid` — random UUID (`_UID` tag), unique, not editable;
  - `child_of_family` — FK to the `Family` where the person is a child
    (`related_name="children"`).
  Indexed on `last_name` and `birth_date`. Helpers: `age` property
  (age at death when deceased, current age otherwise), `gender_icon`
  (CSS icon class), `get_partners()`.
- `Family` — a union: `partner1` / `partner2` (nullable FKs,
  `related_name="unions_as_p1"` / `"unions_as_p2"`), `union_type`
  (MARR/CIVI/COHA/OTHE, default MARR), `union_date`/`union_place`,
  `separation_date`. A `Person` has at most one `child_of_family`, but
  can appear in any number of unions — remarriages are modelled as
  extra `Family` rows.

## GEDCOM (genealogy/utils.py)

- `GedcomParser` (import, built on the `python-gedcom` package):
  - `_ensure_utf8` transcodes the upload to UTF-8 first — it tries
    UTF-8/BOM, then maps the GEDCOM `1 CHAR` tag to a Python codec
    (`ANSEL`/`ANSI`→latin-1, `IBMPC`→cp437, `UNICODE`→utf-16,
    `WINDOWS-1252`→cp1252, unknown→latin-1) since python-gedcom
    hardcodes UTF-8 decoding;
  - two passes: create every `IndividualElement` as a `Person`, then
    every `FamilyElement` as a `Family` linking `HUSB`/`WIFE`/`CHIL`
    pointers through `person_map`;
  - persons are `update_or_create`d **on `gedcom_id`** — re-importing a
    file updates rather than duplicates; `_UID` values are kept (32-hex
    or UUID form) when valid;
  - `_parse_date` accepts `YYYY-MM-DD`, `DD MON YYYY`, then falls back
    to the first 4-digit year (Jan 1st) — GEDCOM dates like
    `ABT 1990` degrade instead of failing.
- `GedcomExporter` (export): emits a GEDCOM 5.5.1, UTF-8 file with a
  CousinsMatter header (`APP_VERSION`, `SITE_NAME`), one
  `0 @I<pk>@ INDI` record per person (name, sex, `_UID`, BIRT/DEAT,
  FAMS/FAMC pointers) and one `0 @F<pk>@ FAM` record per union; the
  pointer uses `person.gedcom_id` when present and falls back to
  `@I{pk}@`. Export is built **in memory** — nothing is written to
  disk; `settings.GEDCOM_FILE` (`genealogy.ged`) only names the
  attachment (`Content-Disposition`) and the `1 FILE` header line.
- `do_import_gedcom` (genealogy/services.py) is the service the view
  calls: save upload to `tmp/` in default storage →
  `transaction.atomic()` around parse (a failure mid-import rolls back
  the partially imported tree) → clear genealogy caches → return
  `(success, message)`; the temp file is deleted in a `finally`.
  Messaging and redirects stay in the view
  (genealogy/views/views_gedcom.py: `genealogy:import_gedcom`,
  `export_gedcom`, `download_gedcom`).

## Family chart, statistics and caching

- `resolve_main_person_id` picks the chart centre: explicit id → the
  per-tenant `family_chart_root_person_id` setting → first `Person`.
- `build_family_chart_data` bounds the graph with
  `_get_bounded_family_graph` to `FAMILY_CHART_GENERATIONS` (settings
  default 4) generations of parents/spouses/children, then serves each
  person's display data plus `rels` (father/mother/spouses/children)
  for the chart widget and hover tooltips; the JSON comes from
  `genealogy:family_chart_data`.
- Chart data is cached behind a **versioned key**
  (`CACHE_KEY_FAMILY_CHART_DATA`, `_v2`): the key holds a generation
  UUID, so deleting it invalidates every per-person entry at once.
- `build_statistics_context` aggregates the statistics page: gender
  distribution, top 10 first/last names, births per decade.
- List views go through `get_people_queryset` / `get_families_queryset`
  — search on names, and sorting via the `PERSON_SORT_FIELDS`
  allowlist (unknown `?sort=` falls back to `name`; guards against
  `order_by` injection).

## Cache invalidation

Any write (`person_create`/`person_update`/`person_delete`, import) calls
`clear_genealogy_caches()` (genealogy/utils.py), which deletes every key
registered by `register_genealogy_cache` (chart + statistics, plus the
template fragment key). `genealogy:refresh` clears them manually.

## URLs and access (URL namespace `genealogy`)

`dashboard` (counts), `people/` CRUD (HTMX-paginated list, 50/page),
`families/` CRUD, `import/`, `export/`, `download-gedcom/` +
`download.ged`, `family-chart/`, `api/family-chart-data/`,
`statistics/`, `refresh/`. Every view is behind the global
`LoginRequiredMiddleware` (core/middleware.py) and nothing else — any
logged-in member can import, export and edit the tree; there is no
admin-only gate in this app.

## See also

- [GEDCOM import/export flow](/flows/gedcom-import-export.md) — the
  end-to-end round trip
- [Members](/apps/members.md) — the `Person.member` account link
- [Tenants](/apps/tenants.md) — shared tree data, per-tenant chart root
- [Core](/apps/core.md) — pagination, cache conventions
