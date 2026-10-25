from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin as DefaultFlatPageAdmin
from django.contrib.flatpages.models import FlatPage as DefaultFlatPage
from django.utils.translation import gettext_lazy as _
from .forms import AdminPageForm
from .models import FlatPage

# Unregister the default FlatPage admin if it's registered
try:
  admin.site.unregister(DefaultFlatPage)
except admin.sites.NotRegistered:
  pass


@admin.register(FlatPage)
class FlatPageAdmin(DefaultFlatPageAdmin):
  form = AdminPageForm
  fieldsets = DefaultFlatPageAdmin.fieldsets + ((_("Sync status"), {"fields": ("predefined", "updated")}),)
  list_display = ("url", "tenant", "title", "predefined", "updated")
  list_select_related = ["tenant"]
  list_filter = ("tenant", "sites", "registration_required", "predefined", "updated")
