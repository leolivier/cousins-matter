from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


def setup_notification_schedules_handler(sender, **kwargs):
  """
  Signal handler to setup notification schedules after migration.
  """
  from .tasks_schedules import setup_notification_schedules

  setup_notification_schedules()


class CousinsMatterConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "core"
  verbose_name = _("Cousins Matter!")

  def ready(self):
    post_migrate.connect(setup_notification_schedules_handler, sender=self)
