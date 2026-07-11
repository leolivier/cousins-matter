from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ChatRoom, ChatMessage, PrivateChatRoom


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
  list_display = ["name", "slug", "date_added", "is_public_room"]
  search_fields = ["name", "slug"]
  list_filter = ["date_added"]
  prepopulated_fields = {"slug": ("name",)}
  date_hierarchy = "date_added"

  @admin.display(description=_("public"), boolean=True)
  def is_public_room(self, obj):
    return obj.is_public


@admin.register(PrivateChatRoom)
class PrivateChatRoomAdmin(admin.ModelAdmin):
  list_display = ["name", "slug", "date_added"]
  search_fields = ["name", "slug"]
  list_filter = ["date_added"]
  filter_horizontal = ["admins"]
  date_hierarchy = "date_added"


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
  list_display = ["member", "room", "date_added", "short_content"]
  list_filter = ["room", "member", "date_added"]
  search_fields = ["content", "member__username", "room__name"]
  readonly_fields = ["date_added"]
  date_hierarchy = "date_added"

  @admin.display(description=_("content"))
  def short_content(self, obj):
    return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
