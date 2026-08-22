"""Hard-delete a tenant and all of its data (compliance / cleanup).

Thin wrapper around :func:`tenants.services.delete_tenant` (shared with the
management UI). Refuses the system tenant and any still-active tenant — a
tenant must be deactivated (soft-deleted) first so the action is deliberate.
"""

from django.core.exceptions import PermissionDenied
from django.core.management.base import BaseCommand, CommandError

from tenants.models import Tenant
from tenants.services import delete_tenant as delete_tenant_service


class Command(BaseCommand):
  help = "Hard-delete a tenant and all its data. Refuses the system and active tenants."

  def add_arguments(self, parser):
    parser.add_argument("slug", help="Slug of the tenant to delete")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")

  def handle(self, *args, **options):
    slug = options["slug"]
    try:
      tenant = Tenant.objects.get(slug=slug)
    except Tenant.DoesNotExist:
      raise CommandError(f"No tenant with slug {slug!r}.")
    name = tenant.name

    # refuse early (before prompting), like the pre-refactor command
    try:
      if tenant.is_system:
        raise PermissionDenied("The system tenant cannot be deleted.")
      if tenant.is_active:
        raise PermissionDenied("This family is still active. Deactivate it before deleting it.")
    except PermissionDenied as e:
      raise CommandError(str(e))

    if not options["yes"]:
      confirm = input(
        f"This will PERMANENTLY delete tenant {slug!r} and ALL its data. Type the slug to confirm: "
      )
      if confirm.strip() != slug:
        raise CommandError("Confirmation did not match. Aborting.")

    try:
      member_count = delete_tenant_service(tenant)
    except PermissionDenied as e:
      raise CommandError(str(e))
    self.stdout.write(
      self.style.SUCCESS(f"Deleted tenant {name!r} ({slug!r}) and {member_count} member(s).")
    )
