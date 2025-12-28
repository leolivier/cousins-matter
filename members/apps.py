from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MembersConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "members"
  verbose_name = _("Members")

  def ready(self):
    # Implicitly connect trace login signal handlers decorated with @receiver.
    from . import trace_login  # NOQA
