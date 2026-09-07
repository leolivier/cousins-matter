from django.contrib import admin

from .models import TenantRequest


@admin.register(TenantRequest)
class TenantRequestAdmin(admin.ModelAdmin):
  list_display = ("email", "tenant_name", "status", "expires_at", "created_at")
  list_filter = ("status",)
  search_fields = ("email", "tenant_name")
