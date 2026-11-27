"""Create a verified database dump, optionally upload it to S3/R2, prune old ones."""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.backup import run_backup


class Command(BaseCommand):
  help = (
    "Dump the database in PostgreSQL custom format, verify the archive, upload it to the "
    "configured S3/R2 bucket and delete dumps older than BACKUP_KEEP_DAYS."
  )

  def add_arguments(self, parser):
    parser.add_argument("--directory", help="Local backup directory (default: BACKUP_DIR).")
    parser.add_argument("--keep-days", type=int, help="Retention in days (default: BACKUP_KEEP_DAYS).")
    parser.add_argument(
      "--no-upload",
      action="store_true",
      help="Keep the dump local even when BACKUP_S3_BUCKET is configured.",
    )

  def handle(self, *args, **options):
    directory = Path(options["directory"]) if options["directory"] else None
    try:
      report = run_backup(
        directory=directory,
        keep_days=options["keep_days"],
        upload_dump=not options["no_upload"],
      )
    except Exception as exc:  # surface any dump/upload failure as a command error
      raise CommandError(f"Database backup failed: {exc}") from exc

    size_mb = report["bytes"] / (1024 * 1024)
    self.stdout.write(self.style.SUCCESS(f"Backup written: {report['file']} ({size_mb:.1f} MiB)"))
    if report["uploaded"]:
      self.stdout.write(self.style.SUCCESS(f"Uploaded to s3://{report['uploaded']}"))
    else:
      self.stdout.write(self.style.WARNING("No remote upload (BACKUP_S3_BUCKET is not configured)."))
    self.stdout.write(f"Pruned {report['local_pruned']} local and {report['remote_pruned']} remote dump(s).")
