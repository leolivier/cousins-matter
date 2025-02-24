#!/usr/bin/env python

from datetime import timedelta
from pathlib import Path
import zipfile
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from members.models import LoginTrace


class Command(BaseCommand):
  help = "Deletes login traces older than settings.LOGIN_HISTORY_PURGE_DAYS days."

  def handle(self, *args, **options):
    a_while_ago = timezone.now() - timedelta(days=settings.LOGIN_HISTORY_PURGE_DAYS)
    # Deletion of logs with a login date prior to LOGIN_HISTORY_PURGE_DAYS days ago
    deleted, _ = LoginTrace.objects.filter(login_at__lt=a_while_ago).delete()
    logfile = self.get_clean_logfile()
    with logfile.open("a") as f:
      f.write(f"{timezone.now()}: LoginTrace purge complete: {deleted} logs older than "
              f"{settings.LOGIN_HISTORY_PURGE_DAYS} days deleted.\n")

  def get_clean_logfile(self):
    db_file = Path(settings.DATABASES['default']['NAME'])
    logfile = db_file.parent / "cron.log"

    if logfile.exists() and logfile.stat().st_size > 1*1024*1024:  # 1MB
      self.stdout.write("Logfile too large, compressing...")
      zipped_logfile = logfile.parent / f"{logfile.name}.zip"
      with zipfile.ZipFile(zipped_logfile, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(logfile)
      logfile.unlink(missing_ok=True)

    return logfile
