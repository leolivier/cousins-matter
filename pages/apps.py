from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pages"
    verbose_name = _("Pages")
