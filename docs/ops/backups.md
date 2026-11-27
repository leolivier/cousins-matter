---
type: Operations Guide
title: Database Backups
description: Daily pg_dump, verified archive, optional R2 upload, retention, and the restore drill
tags: ["ops", "backup", "postgres", "r2"]
status: draft
stale_after: 2027-11-27
generated: { by: claude-code/glm-5.3-flash, at: 2026-11-27T00:00:00Z }
---

# Database Backups

Media lives in the object store (`MEDIA_STORAGE`, Cloudflare R2 in the SaaS
deployment) and is protected by the bucket's own durability. The **database**
is the single copy that has no second home: a lost Postgres volume loses every
family, member, gallery row and subscription snapshot. This page covers the
automated dump and, most importantly, the restore drill.

## What runs

`docker-compose.yml` defines a `backup` service using the application image.
It runs `python manage.py backup_database` at startup, then every 24 hours:

1. `pg_dump --format=custom --compress=9 --no-owner --no-privileges` into
   `BACKUP_DIR` (`/app/backup` in the container, `./backup` on the host);
2. verifies the archive with `pg_restore --list` and rejects an empty file;
3. uploads it to `s3://$BACKUP_S3_BUCKET/$BACKUP_S3_PREFIX/` when a bucket is
   configured (Cloudflare R2 or any S3-compatible endpoint);
4. deletes local and remote dumps older than `BACKUP_KEEP_DAYS` (14 by
   default). Remote pruning only touches `cmm-*.dump` objects under the
   configured prefix.

A failed dump never overwrites a previous one: the partial file is removed and
the command exits non-zero. The compose service logs the failure and retries
the next day.

The image ships `postgresql-client-18` from the PGDG repository because
`pg_dump` must be at least the server's major version (the compose stack runs
PostgreSQL 18). If the server is upgraded, bump the client in the `Dockerfile`
and the `postgres` image together.

## Configuration

| Variable | Default | Role |
|---|---|---|
| `BACKUP_DIR` | `<BASE_DIR>/backup` | local dump directory (mounted from `./backup`) |
| `BACKUP_KEEP_DAYS` | `14` | retention, local and remote |
| `BACKUP_DB_USER` / `BACKUP_DB_PASSWORD` | `POSTGRES_USER` / `POSTGRES_PASSWORD` | dump role; must be the owner, **not** `POSTGRES_RUNTIME_USER` |
| `BACKUP_S3_BUCKET` | `""` | empty = local only |
| `BACKUP_S3_ENDPOINT_URL` | `""` | e.g. `https://<account>.r2.cloudflarestorage.com` |
| `BACKUP_S3_ACCESS_KEY` / `BACKUP_S3_SECRET_KEY` | `""` | R2 API token |
| `BACKUP_S3_REGION` | `auto` | R2 region |
| `BACKUP_S3_PREFIX` | `db-backups` | object prefix |

When the SaaS runs with row-level security (`POSTGRES_RUNTIME_USER`), the app
connects as a restricted role. `pg_dump` still needs the owner (or a role with
`BYPASSRLS` and read on every table), hence the separate `BACKUP_DB_*`
variables. Leave them empty in a mono-tenant deployment: they fall back to
`POSTGRES_USER`.

The host `./backup` directory must be writable by `cm_user` (UID 1000 in the
image). Create it once with `mkdir -p backup && sudo chown 1000:1000 backup`.

## Manual run

```bash
docker compose run --rm --entrypoint python backup manage.py backup_database
# or, on an existing container:
docker compose exec backup python manage.py backup_database --no-upload
```

`--directory`, `--keep-days` and `--no-upload` override the settings.

## Restore drill (run monthly)

A backup that has never been restored is a hope, not a backup. Do this on the
VPS, without touching the production database:

```bash
# 1. create a scratch database (the owner role is the one from POSTGRES_USER)
docker compose exec -T postgres createdb -U "$POSTGRES_USER" -O "$POSTGRES_USER" cmm_restore_test

# 2. restore the most recent dump (it is visible at /backup inside postgres)
docker compose exec -T postgres pg_restore -U "$POSTGRES_USER" -d cmm_restore_test \
  --clean --if-exists --no-owner /backup/$(ls -t backup | head -1)

# 3. sanity checks
docker compose exec -T postgres psql -U "$POSTGRES_USER" -d cmm_restore_test -c \
  'select (select count(*) from tenants_tenant) as tenants, (select count(*) from members_member) as members, (select count(*) from galleries_photo) as photos;'

# 4. drop the scratch database
docker compose exec -T postgres dropdb -U "$POSTGRES_USER" cmm_restore_test
```

Record the counts and the dump date somewhere (release ticket, runbook). A
monthly 2-minute drill is what turns a backup into a recoverable system.

To restore from R2 (when the VPS itself is gone), download the object first:

```bash
rclone copy r2:<bucket>/db-backups/cmm-20261127T030000Z.dump ./backup/
# or: aws s3 cp s3://<bucket>/db-backups/<file> ./backup/ --endpoint-url https://<account>.r2.cloudflarestorage.com
```

Then follow the same `pg_restore` steps on a fresh stack. Restore into a
**new** database and point `POSTGRES_DB` at it only after the sanity checks.

## R2 side

- Enable **object versioning** (and, on R2, consider Object Lock) on the
  bucket: an application bug or a retention deletion must not be able to erase
  history immediately.
- Keep the backup prefix separate from media (`db-backups/`), and give the
  backup token write access only to that prefix when possible.
- Media and database dumps must not share the same lifecycle rule that expires
  objects after a few days.

## Monitoring

- A backup failure only appears in the `backup` container's logs. Ship those
  logs somewhere you read, or add an uptime check on the dump age.
- The application exposes `/health` (database + Redis) and `/qhealth`
  (Django-Q round trip); point an external uptime monitor at both.
- `SENTRY_DSN` enables error tracking in production (no personal data is
  sent). Without it, Django exceptions only reach `docker compose logs`.
