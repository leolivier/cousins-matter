from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Member, Family, Address, LoginTrace


class ReadOnlyModelAdmin(admin.ModelAdmin):
  actions = None

  def has_add_permission(self, request):
    return False

  def has_change_permission(self, request, obj=None):
    return False

  def has_delete_permission(self, request, obj=None):
    return False


@admin.register(Member)
class MemberAdmin(UserAdmin):
  list_display = ["username", "email", "first_name", "last_name", "birthdate", "is_active", "avatar_preview"]
  list_filter = ["is_active", "is_staff", "is_superuser", "family", "birthdate"]
  search_fields = ["username", "first_name", "last_name", "email"]
  raw_id_fields = ["address", "family", "member_manager"]
  filter_horizontal = ["groups", "user_permissions", "followers"]

  fieldsets = UserAdmin.fieldsets + (
    (_("Extra Profile Info"), {"fields": ("avatar", "birthdate", "phone", "address", "family", "website", "description", "hobbies")}),
    (_("Privacy & Management"), {"fields": ("privacy_consent", "member_manager", "is_dead", "deathdate", "email_batch_frequency")}),
  )

  def avatar_preview(self, obj):
    if obj.avatar:
      return format_html('<img src="{}" style="max-height: 30px; border-radius: 50%;"/>', obj.avatar.url)
    return ""

  avatar_preview.short_description = _("avatar")


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
  list_display = ["name", "parent"]
  search_fields = ["name"]
  list_filter = ["parent"]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
  list_display = ["number_and_street", "city", "zip_code", "country"]
  search_fields = ["number_and_street", "city", "zip_code", "country"]
  list_filter = ["country", "city"]


@admin.register(LoginTrace)
class LoginTraceAdmin(ReadOnlyModelAdmin):
  list_display = ["user", "ip", "login_at", "logout_at", "country_code"]
  list_filter = ["login_at", "country_code"]
  search_fields = ["user__username", "ip"]
  date_hierarchy = "login_at"
