from django.apps import AppConfig
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _


def seed_pages_on_tenant_create(sender, instance, created, **kwargs):
  """Seed a freshly created tenant with its own copy of the predefined pages.

  Module-level so the signal's weak reference stays alive for the whole
  process: a receiver defined inside ``ready()`` would be garbage-collected
  (signals hold receivers weakly) and the seeding would silently stop.
  """
  if created:
    from .services import seed_tenant_pages  # local import: models must not load before the registry

    seed_tenant_pages(instance)


class PageConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "pages"
  verbose_name = _("Pages")

  def ready(self):
    # every freshly created tenant gets its own editable copy of the
    # predefined pages — whatever the creation path (signup view, admin,
    # ORM). Previously only the signup view seeded them, leaving tenants
    # created elsewhere (e.g. Django admin) without a family home page.
    from tenants.models import Tenant

    post_save.connect(seed_pages_on_tenant_create, sender=Tenant, dispatch_uid="pages.seed_on_tenant_create")
