"""Django admin registration for tenants.

The admin is the platform-admin (``is_staff``) control panel: create new
tenants, toggle ``is_active`` (soft-delete), and edit per-tenant settings.
Tenant admins (``Member.role == "admin"``) are NOT Django-admin users, so they
cannot reach this — only platform superusers can create or deactivate tenants.
"""

from django.contrib import admin

from .models import Tenant, TenantSettings


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
  list_display = ("name", "slug", "is_active", "created_at", "updated_at")
  list_filter = ("is_active",)
  search_fields = ("name", "slug")
  ordering = ("name",)
  readonly_fields = ("created_at", "updated_at")


@admin.register(TenantSettings)
class TenantSettingsAdmin(admin.ModelAdmin):
  list_display = ("tenant",)
  search_fields = ("tenant__name", "tenant__slug")
