from django.contrib import admin

from .models import Family, Person


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
  list_display = ["first_name", "last_name", "birth_date", "sex", "get_member_link"]
  list_filter = ["sex"]
  search_fields = ["first_name", "last_name", "gedcom_id"]
  raw_id_fields = ["child_of_family", "member"]

  def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related("child_of_family", "member")

  def get_member_link(self, obj):
    return str(obj.member) if obj.member else "-"

  get_member_link.short_description = "Linked Member"


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
  list_display = ["get_partner1_name", "get_partner2_name", "union_type", "union_date"]
  list_filter = ["union_type"]
  search_fields = ["partner1__first_name", "partner1__last_name", "partner2__first_name", "partner2__last_name"]
  raw_id_fields = ["partner1", "partner2"]

  def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related("partner1", "partner2")

  def get_partner1_name(self, obj):
    return str(obj.partner1) if obj.partner1 else "-"

  get_partner1_name.short_description = "Partner 1"

  def get_partner2_name(self, obj):
    return str(obj.partner2) if obj.partner2 else "-"

  get_partner2_name.short_description = "Partner 2"
