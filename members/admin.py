from django.contrib import admin

from .models import Member, Family, Address, LoginTrace


class ReadOnlyModelAdmin(admin.ModelAdmin):
  actions = None
  model = LoginTrace

  def has_add_permission(self, request):
    return False

    def has_change_permission(self, request, obj=None):
        return request.method in ["GET", "HEAD"] and super().has_change_permission(
            request, obj
        )

  def has_delete_permission(self, request, obj=None):
    return False


# Register your models here.
admin.site.register(LoginTrace, ReadOnlyModelAdmin)
admin.site.register(Member)
admin.site.register(Family)
admin.site.register(Address)
