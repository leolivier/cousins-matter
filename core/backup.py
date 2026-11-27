"""Database backups: ``pg_dump``, optional S3/R2 upload, retention and integrity check.

The dump is written in PostgreSQL's custom format (compressed, restorable with
``pg_restore``), verified by listing its table of contents, then optionally
uploaded to an S3-compatible bucket (Cloudflare R2 by default). Old dumps are
pruned locally and remotely by age.

The command must run with a client whose major version matches the server
(``postgresql-client-18`` is installed in the image) and with the *owner*
database role, not the RLS-restricted runtime role: use ``BACKUP_DB_USER`` /
``BACKUP_DB_PASSWORD`` when ``POSTGRES_RUNTIME_USER`` is configured.
"""

import logging
import os
import subprocess  # nosec B404 - required to run pg_dump/pg_restore
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

FILENAME_PATTERN = "cmm-*.dump"
BACKUP_PREFIX = "cmm-"


class BackupError(Exception):
  """A backup step failed; the message is safe for operators."""


def backup_filename(now: datetime | None = None) -> str:
  now = now or datetime.now(UTC)
  return f"cmm-{now:%Y%m%dT%H%M%SZ}.dump"


def _db_config() -> dict[str, str]:
  db = settings.DATABASES["default"]
  return {
    "host": str(db.get("HOST") or "localhost"),
    "port": str(db.get("PORT") or "5432"),
    "name": str(db["NAME"]),
    "user": settings.BACKUP_DB_USER or str(db["USER"]),
    "password": settings.BACKUP_DB_PASSWORD or str(db.get("PASSWORD") or ""),
  }


def create_dump(target: Path, timeout: int = 3600) -> Path:
  """Dump the database to ``target`` and verify the archive; remove it on failure."""
  config = _db_config()
  command = [
    "pg_dump",
    "--format=custom",
    "--compress=9",
    "--no-owner",
    "--no-privileges",
    "--host",
    config["host"],
    "--port",
    config["port"],
    "--username",
    config["user"],
    "--dbname",
    config["name"],
    "--file",
    str(target),
  ]
  env = {**os.environ, "PGPASSWORD": config["password"]}
  try:
    # fixed argv list, no shell; paths come from settings, never from a request
    subprocess.run(command, check=True, env=env, timeout=timeout, capture_output=True, text=True)  # nosec B603
    subprocess.run(  # nosec B603 B607 - fixed argv list, no shell, path from settings
      ["pg_restore", "--list", str(target)],
      check=True,
      timeout=120,
      capture_output=True,
      text=True,
    )
  except (OSError, subprocess.SubprocessError) as exc:
    target.unlink(missing_ok=True)
    stderr = getattr(exc, "stderr", "") or ""
    raise BackupError(f"pg_dump failed: {stderr.strip() or exc}") from exc
  if target.stat().st_size < 1024:
    target.unlink(missing_ok=True)
    raise BackupError("pg_dump produced an empty dump")
  return target


def prune_local(directory: Path, keep_days: int, now: datetime | None = None) -> int:
  """Delete local dumps older than ``keep_days``; returns the number removed."""
  cutoff = (now or datetime.now(UTC)) - timedelta(days=keep_days)
  removed = 0
  for path in directory.glob(FILENAME_PATTERN):
    try:
      modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    except OSError:
      continue
    if modified < cutoff and path.is_file():
      path.unlink(missing_ok=True)
      removed += 1
  return removed


def _bucket() -> str:
  return getattr(settings, "BACKUP_S3_BUCKET", "") or ""


def _prefix() -> str:
  return (getattr(settings, "BACKUP_S3_PREFIX", "") or "").strip("/")


def remote_key(filename: str) -> str:
  prefix = _prefix()
  return f"{prefix}/{filename}" if prefix else filename


def s3_client():
  """Build a boto3 S3 client for R2 (or any S3-compatible endpoint)."""
  import boto3

  return boto3.client(
    "s3",
    endpoint_url=getattr(settings, "BACKUP_S3_ENDPOINT_URL", "") or None,
    aws_access_key_id=getattr(settings, "BACKUP_S3_ACCESS_KEY", "") or None,
    aws_secret_access_key=getattr(settings, "BACKUP_S3_SECRET_KEY", "") or None,
    region_name=getattr(settings, "BACKUP_S3_REGION", "auto") or "auto",
  )


def upload(path: Path, client: Any = None) -> str:
  """Upload one dump; returns its object key."""
  bucket = _bucket()
  if not bucket:
    raise BackupError("BACKUP_S3_BUCKET is not configured")
  client = client or s3_client()
  key = remote_key(path.name)
  client.upload_file(str(path), bucket, key)
  logger.info("Backup %s uploaded to s3://%s/%s", path.name, bucket, key)
  return key


def prune_remote(client: Any, keep_days: int, now: datetime | None = None) -> int:
  """Delete remote dumps older than ``keep_days`` (only our own objects)."""
  bucket = _bucket()
  if not bucket:
    return 0
  cutoff = (now or datetime.now(UTC)) - timedelta(days=keep_days)
  prefix = remote_key("")
  deleted = 0
  stale: list[dict[str, str]] = []

  def flush() -> None:
    nonlocal deleted
    if stale:
      client.delete_objects(Bucket=bucket, Delete={"Objects": list(stale)})
      deleted += len(stale)
      stale.clear()

  paginator = client.get_paginator("list_objects_v2")
  for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
    for obj in page.get("Contents", []):
      name = obj["Key"].rsplit("/", 1)[-1]
      if not name.startswith(BACKUP_PREFIX) or not name.endswith(".dump"):
        continue
      modified = obj["LastModified"]
      if modified.tzinfo is None:  # some S3-compatible endpoints omit the zone
        modified = modified.replace(tzinfo=UTC)
      if modified < cutoff:
        stale.append({"Key": obj["Key"]})
        if len(stale) == 1000:
          flush()
  flush()
  return deleted


def run_backup(
  directory: Path | None = None,
  keep_days: int | None = None,
  upload_dump: bool = True,
  now: datetime | None = None,
) -> dict:
  """Create, verify, upload and prune one dump; returns a small report."""
  now = now or datetime.now(UTC)
  directory = Path(directory or settings.BACKUP_DIR)
  keep_days = settings.BACKUP_KEEP_DAYS if keep_days is None else keep_days
  directory.mkdir(parents=True, exist_ok=True)
  target = directory / backup_filename(now)

  create_dump(target)
  local_pruned = prune_local(directory, keep_days, now)

  uploaded = None
  remote_pruned = 0
  if upload_dump and _bucket():
    client = s3_client()
    uploaded = upload(target, client)
    remote_pruned = prune_remote(client, keep_days, now)
  elif upload_dump:
    logger.warning("BACKUP_S3_BUCKET is not configured; keeping the dump locally only")

  return {
    "file": str(target),
    "bytes": target.stat().st_size,
    "uploaded": uploaded,
    "local_pruned": local_pruned,
    "remote_pruned": remote_pruned,
  }
