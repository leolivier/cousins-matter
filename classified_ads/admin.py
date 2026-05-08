from django.contrib import admin

from .models import AdPhoto, ClassifiedAd


@admin.register(ClassifiedAd)
class ClassifiedAdAdmin(admin.ModelAdmin):
  list_display = ["title", "owner", "category", "subcategory", "ad_status", "price", "date_created"]
  list_filter = ["ad_status", "category", "date_created"]
  search_fields = ["title", "description", "owner__username"]
  list_select_related = ["owner"]  # Évite N+1 sur la relation owner
  date_hierarchy = "date_created"
  ordering = ["-date_created"]


@admin.register(AdPhoto)
class AdPhotoAdmin(admin.ModelAdmin):
  list_display = ["id", "ad", "image"]
  list_select_related = ["ad", "ad__owner"]  # Évite N+1 sur les relations ad et owner
  search_fields = ["ad__title"]
  raw_id_fields = ["ad"]  # Améliore les performances pour la sélection d'annonces
