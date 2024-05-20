from django.contrib import admin

from .models import News, NewsContent, Comment

admin.site.register(News)
admin.site.register(NewsContent)
admin.site.register(Comment)
