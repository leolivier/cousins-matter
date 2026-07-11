from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Trove


@admin.register(Trove)
class TroveAdmin(admin.ModelAdmin):
  list_display = ["title", "category", "owner", "picture_preview"]
  list_select_related = ["owner"]
  list_filter = ["category", "owner"]
  search_fields = ["title", "description"]
  readonly_fields = ["thumbnail"]
  raw_id_fields = ["owner"]

  @admin.display(description=_("preview"))
  def picture_preview(self, obj):
    if obj.thumbnail:
      return format_html('<img src="{}" style="max-height: 50px;"/>', obj.thumbnail.url)
    return ""
