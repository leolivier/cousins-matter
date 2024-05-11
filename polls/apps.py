from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PollsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'polls'
    verbose_name = _("Polls")
