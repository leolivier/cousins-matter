from django.contrib import admin
from .models import AdPhoto, ClassifiedAd


class AdPhotoInline(admin.TabularInline):
  model = AdPhoto
  extra = 1
  fields = ["image", "thumbnail"]
  readonly_fields = ["thumbnail"]


@admin.register(ClassifiedAd)
class ClassifiedAdAdmin(admin.ModelAdmin):
  list_display = ["title", "owner", "category", "subcategory", "ad_status", "price", "date_created"]
  list_filter = ["ad_status", "category", "date_created"]
  search_fields = ["title", "description", "owner__username"]
  list_select_related = ["owner"]  # Avoid N+1 on owner relationship
  date_hierarchy = "date_created"
  ordering = ["-date_created"]
  inlines = [AdPhotoInline]


@admin.register(AdPhoto)
class AdPhotoAdmin(admin.ModelAdmin):
  list_display = ["id", "ad", "image"]
  list_select_related = ["ad", "ad__owner"]  # Avoid N+1 on ad and owner relationships
  search_fields = ["ad__title"]
  raw_id_fields = ["ad"]  # Improve performance for ad selection
