from django.contrib import admin
from .models import Family, Person


class PersonInline(admin.TabularInline):
  model = Person
  fields = ["first_name", "last_name", "sex", "birth_date"]
  extra = 0
  show_change_link = True


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
  list_display = ["first_name", "last_name", "birth_date", "sex", "member"]
  list_filter = ["sex", "birth_date"]
  search_fields = ["first_name", "last_name", "gedcom_id"]
  raw_id_fields = ["child_of_family", "member"]

  def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related("child_of_family", "member")


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
  list_display = ["partner1", "partner2", "union_type", "union_date"]
  list_filter = ["union_type", "union_date"]
  search_fields = ["partner1__first_name", "partner1__last_name", "partner2__first_name", "partner2__last_name"]
  raw_id_fields = ["partner1", "partner2"]
  inlines = [PersonInline]

  def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related("partner1", "partner2")
