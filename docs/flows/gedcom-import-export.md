---
type: Flow
title: GEDCOM Import/Export
description: End-to-end GEDCOM round trip — upload and parse into Person/Family, error rollback, and in-memory export back to GEDCOM 5.5.1
tags: ["flow", "genealogy"]
status: draft
stale_after: 2027-03-05
generated: { by: claude-code/glm-5.3-flash, at: 2026-09-05T11:39:00Z }
---

# GEDCOM Import/Export

GEDCOM is the front door for real genealogy data: a single file upload
populates (or updates) the whole family tree, and the tree can be exported
back to GEDCOM 5.5.1. The data model (`Person`, `Family`) is covered in
[Genealogy](/apps/genealogy.md); this fiche is the round trip.

## Import

1. **Entry point.** From the genealogy dashboard, `GET /genealogy/import/`
   (genealogy/urls.py, `name="import_gedcom"`) renders
   `genealogy/import_gedcom.html` with
   `genealogy/forms.py: GedcomImportForm` (single `gedcom_file` field,
   `.ged` accept attribute). Login is enforced globally by
   `core/middleware.py: LoginRequiredMiddleware` — there is no per-view
   permission check, so any logged-in member can import.
2. **Upload.** `POST /genealogy/import/` →
   `genealogy/views/views_gedcom.py: import_gedcom` validates the form and
   hands the upload to `genealogy/services.py: do_import_gedcom`.
3. **Staging.** `do_import_gedcom` writes the upload to
   `default_storage.save("tmp/<name>")`, deletes it in a `finally` block —
   the file never outlives the request.
4. **Parsing.** `genealogy/utils.py: GedcomParser` wraps the
   `python-gedcom` package. Because that package hardcodes UTF-8,
   `_ensure_utf8` first tries `utf-8-sig`, then maps the GEDCOM `1 CHAR` tag
   (ANSEL/ANSI→latin-1, UNICODE→utf-16, IBMPC→cp437, WINDOWS-1252→cp1252,
   unknown→latin-1) and transcodes to UTF-8.
5. **DB writes, all or nothing.** `parse()` runs inside
   `transaction.atomic()`:
   - First pass over `IndividualElement`s →
     `Person.objects.update_or_create(gedcom_id=...)` with name, sex
     (M/F, anything else → O), birth/death date+place and the optional
     `_UID` tag as UUID. **Re-importing the same file updates the existing
     persons rather than duplicating them.**
   - Second pass over `FamilyElement`s →
     `_find_or_create_family` matches an existing `Family` on
     (partner1, partner2) or creates one (`union_type="MARR"`), then links
     children by setting `Person.child_of_family`.
   - Dates are parsed leniently: `YYYY-MM-DD`, `DD Mon YYYY`, else the first
     4-digit year (as Jan 1st). Anything else → `None`.
6. **Cache + feedback.** On success
   `genealogy/utils.py: clear_genealogy_caches()` drops the registered
   (template-fragment) caches, a success message is flashed and the user is
   redirected to `genealogy:dashboard`. **Side effects:** Person/Family rows
   created or updated platform-wide, caches invalidated, temp file removed.

## Export

1. **Entry points.** `GET /genealogy/export/` (`export_gedcom`) returns the
   file as an attachment named `settings.GEDCOM_FILE` (default
   `genealogy.ged`); `GET /genealogy/download-gedcom/` (also
   `/genealogy/download.ged`) returns the same content as `text/plain`.
   Both build the content on the fly — nothing is written to disk.
2. **Generation.** `genealogy/utils.py: GedcomExporter.export` concatenates:
   a GEDCOM 5.5.1 header (`_get_gedcom_header`, includes `DEST`/`SOUR
   CousinsMatter`, `APP_VERSION`, site name and the current Person/Family
   counts), one `0 @I<n>@ INDI` block per person (pointer = `gedcom_id` when
   present, else `@I<pk>@`; `_UID` from `person.uid`), one `FAM` block per
   family, and `0 TRLR`. **Scope note:** the export covers **all** persons
   and families — `Person`/`Family` are not tenant-scoped
   ([Tenants](/apps/tenants.md)), so the export is a whole-platform tree.

## Failure modes visible to the user

- Form rejects anything the browser didn't filter (no `.ged` extension passes
  only if the widget is bypassed — there is no server-side extension
  validator, only the accept hint): an unparseable file surfaces as
  "Error importing GEDCOM: <exception>" flashed by `import_gedcom`, with the
  transaction rolled back — **no partial import**.
- Unknown encodings are transcoded with `errors="replace"`, so mojibake is
  possible on exotic files instead of a hard failure.
- `GEDCOM` dates that defeat the lenient parser are silently dropped
  (`birth_date`/`death_date` = `None`).
- Import and export are synchronous requests: a very large file blocks the
  worker (unlike the gallery zip import, there is no progress bar).

## Related

- [Genealogy app](/apps/genealogy.md) — Person/Family model, chart, statistics.
- [Tenants app](/apps/tenants.md) — why genealogy is *not* tenant-scoped.
- [Gallery Bulk Import flow](/flows/gallery-bulk-import.md) — the async
  counterpart for zip uploads.
