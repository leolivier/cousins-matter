from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Gallery, Photo


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
  list_display = ["name", "parent", "owner", "short_description"]
  search_fields = ["name", "description"]
  list_filter = ["parent", "owner"]
  prepopulated_fields = {"slug": ("name",)}
  raw_id_fields = ["cover", "owner"]

  @admin.display(description=_("description"))
  def short_description(self, obj):
    return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
  list_display = ["name", "gallery", "uploaded_by", "date", "image_preview"]
  list_filter = ["gallery", "uploaded_by", "date"]
  search_fields = ["name", "description"]
  prepopulated_fields = {"slug": ("name",)}
  raw_id_fields = ["gallery", "uploaded_by"]
  date_hierarchy = "date"

  @admin.display(description=_("preview"))
  def image_preview(self, obj):
    if obj.thumbnail:
      return format_html('<img src="{}" style="max-height: 50px;"/>', obj.thumbnail.url)
    return ""
