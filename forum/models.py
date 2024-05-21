import logging
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from members.models import Member

logger = logging.getLogger(__name__)


class Message(models.Model):
  author = models.ForeignKey(Member, on_delete=models.CASCADE)
  date = models.DateTimeField(auto_now=True)
  content = models.TextField(_('Content'), max_length=settings.MESSAGE_MAX_SIZE)
  post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True)

  class Meta:
    ordering = ['date']
    indexes = [
            models.Index(fields=["post", "author"]),
    ]


class Post(models.Model):
  title = models.CharField(_('Title'), max_length=120)
  first_message = models.ForeignKey(Message, related_name='first_of_post', on_delete=models.CASCADE)

  class Meta:
    verbose_name_plural = _('posts')
    ordering = ['first_message__date']
    indexes = [
            models.Index(fields=["title"]),
    ]


class Comment(models.Model):
  author = models.ForeignKey(Member, on_delete=models.CASCADE)
  date = models.DateTimeField(auto_now=True)
  message = models.ForeignKey(Message, on_delete=models.CASCADE)
  content = models.CharField(_('Comment'), max_length=settings.MESSAGE_COMMENTS_MAX_SIZE)

  class Meta:
    verbose_name_plural = _('comments')
    ordering = ['message', 'date']
    indexes = [
            models.Index(fields=["message", "author"]),
    ]
