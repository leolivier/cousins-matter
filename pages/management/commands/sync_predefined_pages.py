"""Re-synchronize tenants' predefined pages (idempotent seed)."""

from django.core.management.base import BaseCommand, CommandError

from pages.services import seed_tenant_pages
from tenants.models import Tenant


class Command(BaseCommand):
  help = (
    "Create missing predefined pages for one tenant (--tenant SLUG) or all tenants. "
    "Idempotent: existing pages are left untouched."
  )

  def add_arguments(self, parser):
    parser.add_argument("--tenant", help="Tenant slug; defaults to all tenants.")

  def handle(self, *args, **options):
    tenants = Tenant.objects.all()
    if options["tenant"]:
      tenants = tenants.filter(slug=options["tenant"])
      if not tenants.exists():
        raise CommandError(f"Unknown tenant: {options['tenant']}")
    for tenant in tenants:
      count = seed_tenant_pages(tenant)
      self.stdout.write(self.style.SUCCESS(f"{tenant.slug}: {count} pages"))
