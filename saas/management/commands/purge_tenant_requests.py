from django.core.management.base import BaseCommand

from ...services import purge_tenant_requests


class Command(BaseCommand):
  help = "Delete expired PENDING and stale VALIDATED/EXPIRED tenant requests."

  def handle(self, *args, **options):
    deleted = purge_tenant_requests()
    self.stdout.write(f"Deleted {deleted} tenant request(s).")
