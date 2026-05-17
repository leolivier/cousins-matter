from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin as DefaultFlatPageAdmin
from django.contrib.flatpages.models import FlatPage as DefaultFlatPage
from django.utils.translation import gettext_lazy as _
from .models import FlatPage

# Unregister the default FlatPage admin if it's registered
try:
  admin.site.unregister(DefaultFlatPage)
except admin.sites.NotRegistered:
  pass


@admin.register(FlatPage)
class FlatPageAdmin(DefaultFlatPageAdmin):
  fieldsets = DefaultFlatPageAdmin.fieldsets + ((_("Sync status"), {"fields": ("predefined", "updated")}),)
  list_display = ("url", "title", "predefined", "updated")
  list_filter = ("sites", "registration_required", "predefined", "updated")
