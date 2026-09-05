from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TenantsConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "tenants"
  verbose_name = _("Tenants")

  def ready(self):
    from . import models as tenants_models  # noqa: F401  (registers signal handlers)

    # Importing the models module connects the post_migrate / setting_changed
    # cache-reset signal handlers declared at its bottom.
