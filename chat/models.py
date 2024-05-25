from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from django.utils.html import escape


class ChatRoom(models.Model):
  name = models.CharField(max_length=255)
  slug = models.CharField(max_length=255, blank=True)
  date_added = models.DateTimeField(auto_now_add=True)

  class Meta:
    verbose_name = _('chat room')
    verbose_name_plural = _('chat rooms')
    ordering = ('date_added',)
    constraints = [
      models.UniqueConstraint(fields=(["slug"]), name="chat room slugs must be unique"),
    ]
    indexes = [
      models.Index(fields=["slug"]),
    ]

  def __str__(self):
    return self.name

  def clean(self):
    self.slug = slugify(self.name)
    if ChatRoom.objects.filter(name=self.name).exists():
      raise ValidationError(_('Another room with the same name already exists'))

    slug_room = ChatRoom.objects.filter(slug=self.slug)
    if slug_room.exists():
      slug_name = escape(slug_room.first().name)
      raise ValidationError(
        _(f"Another room with a similar name already exists ('{slug_name}'). Please choose a different name."))

  def save(self, *args, **kwargs):
    self.full_clean()
    super().save(*args, **kwargs)


class ChatMessage(models.Model):
  account = models.ForeignKey(User, on_delete=models.DO_NOTHING)
  room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
  content = models.TextField(_('message'), max_length=2*1024*1024)
  date_added = models.DateTimeField(auto_now_add=True)

  class Meta:
    ordering = ('date_added',)
    indexes = [
            models.Index(fields=["room"]),
    ]

  def __str__(self):
    room = self.room.name if len(self.room.name) < 20 else f'{self.room.name[:20]}...'
    msg = self.content if len(self.content) < 100 else f'{self.content[:100]}...'
    return f'{room}:{msg}'
