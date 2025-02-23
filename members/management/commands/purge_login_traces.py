#!/usr/bin/env python

from datetime import timedelta
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
    self.stdout.write(f"LoginTrace purge complete: {deleted} logs older than "
                      f"{settings.LOGIN_HISTORY_PURGE_DAYS} days deleted.")
