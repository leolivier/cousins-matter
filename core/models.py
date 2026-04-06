from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings


class NotificationEvent(models.Model):
  member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_events")

  # The object being followed (e.g., ChatRoom, Post)
  followed_content_type = models.ForeignKey(
    ContentType, on_delete=models.CASCADE, related_name="notification_followed_objects"
  )
  followed_object_id = models.PositiveIntegerField()
  followed_object = GenericForeignKey("followed_content_type", "followed_object_id")

  # The new object that triggered the notification (e.g., Message, Comment)
  # Can be the same as followed_object for creation events.
  new_content_type = models.ForeignKey(
    ContentType, on_delete=models.CASCADE, related_name="notification_new_objects", null=True, blank=True
  )
  new_object_id = models.PositiveIntegerField(null=True, blank=True)
  new_object = GenericForeignKey("new_content_type", "new_object_id")

  author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="authored_notification_events")

  followed_object_url = models.URLField(max_length=500)
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    ordering = ["created_at"]
    indexes = [
      models.Index(fields=["member", "created_at"]),
    ]
