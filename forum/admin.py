from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Post, Message, Comment


class MessageInline(admin.TabularInline):
  model = Message
  extra = 1
  fields = ["author", "content"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
  list_display = ["title", "tenant", "owner", "created_date"]
  list_select_related = ["tenant", "first_message", "first_message__author"]
  search_fields = ["title"]
  inlines = [MessageInline]
  raw_id_fields = ["first_message"]
  filter_horizontal = ["followers"]
  list_filter = ["tenant"]

  @admin.display(description=_("created"))
  def created_date(self, obj):
    return obj.first_message.created if obj.first_message else None


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
  list_display = ["author", "post", "created", "short_content", "tenant"]
  list_select_related = ["author", "post", "tenant"]
  list_filter = ["tenant", "post", "author", "created"]
  search_fields = ["content", "author__username", "post__title"]
  date_hierarchy = "created"

  @admin.display(description=_("content"))
  def short_content(self, obj):
    return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
  list_display = ["author", "message", "created", "short_content", "tenant"]
  list_select_related = ["author", "message", "tenant"]
  list_filter = ["tenant", "author", "created"]
  search_fields = ["content", "author__username"]
  date_hierarchy = "created"

  @admin.display(description=_("content"))
  def short_content(self, obj):
    return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
