from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Post, Message, Comment


class MessageInline(admin.TabularInline):
  model = Message
  extra = 1
  fields = ["author", "content"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
  list_display = ["title", "owner", "created_date"]
  search_fields = ["title"]
  inlines = [MessageInline]
  raw_id_fields = ["first_message"]
  filter_horizontal = ["followers"]

  def created_date(self, obj):
    return obj.first_message.created if obj.first_message else None

  created_date.short_description = _("created")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
  list_display = ["author", "post", "created", "short_content"]
  list_filter = ["post", "author", "created"]
  search_fields = ["content", "author__username", "post__title"]
  date_hierarchy = "created"

  def short_content(self, obj):
    return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

  short_content.short_description = _("content")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
  list_display = ["author", "message", "created", "short_content"]
  list_filter = ["author", "created"]
  search_fields = ["content", "author__username"]
  date_hierarchy = "created"

  def short_content(self, obj):
    return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

  short_content.short_description = _("content")
