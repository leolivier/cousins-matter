from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PageConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "pages"
  verbose_name = _("Pages")

  def ready(self):
    # every freshly created tenant gets its own editable copy of the
    # predefined pages — whatever the creation path (signup view, admin,
    # ORM). Previously only the signup view seeded them, leaving tenants
    # created elsewhere (e.g. Django admin) without a family home page.
    import logging

    from django.db.models.signals import post_save

    from tenants.models import Tenant

    from .services import seed_tenant_pages

    logger = logging.getLogger(__name__)

    def seed_pages_on_tenant_create(sender, instance, created, **kwargs):
      if created:
        logger.info(f"pages signal: tenant created ({instance.slug}), seeding pages")
        seed_tenant_pages(instance)
      else:
        logger.info(f"pages signal: post_save created={created} slug={instance.slug}")

    post_save.connect(seed_pages_on_tenant_create, sender=Tenant, dispatch_uid="pages.seed_on_tenant_create")
