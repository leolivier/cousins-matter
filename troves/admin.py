from django.contrib import admin

from .models import Trove


@admin.register(Trove)
class TroveAdmin(admin.ModelAdmin):
  list_display = ["title", "category", "owner"]
  list_select_related = ["owner"]
  list_filter = ["category"]
  search_fields = ["title", "description"]
  readonly_fields = ["thumbnail"]
