from django.apps import AppConfig
from django.db.models.signals import post_migrate


def setup_purge_schedule_handler(sender, **kwargs):
  from .services import setup_purge_schedule

  setup_purge_schedule()


class SaasConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "saas"

  def ready(self):
    # schedule the nightly purge the same way core schedules notifications
    post_migrate.connect(setup_purge_schedule_handler, sender=self)
