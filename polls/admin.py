from django.contrib import admin

from .models import Poll, Question

admin.site.register(Poll)
admin.site.register(Question)
