import logging
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from members.models import Member
logger = logging.getLogger(__name__)


class NewsContent(models.Model):
  author = models.ForeignKey(Member, on_delete=models.CASCADE)
  date = models.DateTimeField(auto_now=True)
  content = models.TextField(_('Content'), max_length=settings.NEWS_MAX_SIZE)
  news = models.ForeignKey('News', on_delete=models.CASCADE, null=True, blank=True)

  class Meta:
    ordering = ['date']
    indexes = [
            models.Index(fields=["news", "author"]),
    ]


class News(models.Model):
  title = models.CharField(_('Title'), max_length=120)
  first_content = models.ForeignKey(NewsContent, related_name='news_first', on_delete=models.CASCADE)

  class Meta:
    verbose_name_plural = _('news')
    ordering = ['first_content__date']
    indexes = [
            models.Index(fields=["title"]),
    ]


class Comment(models.Model):
  author = models.ForeignKey(Member, on_delete=models.CASCADE)
  date = models.DateTimeField(auto_now=True)
  news_content = models.ForeignKey(NewsContent, on_delete=models.CASCADE)
  content = models.CharField(_('Comment'), max_length=settings.NEWS_COMMENTS_MAX_SIZE)

  class Meta:
    verbose_name_plural = _('comments')
    ordering = ['news_content', 'date']
    indexes = [
            models.Index(fields=["news_content", "author"]),
    ]
