from django.contrib import admin

from .models import EventPlanner, Poll, Question, PollAnswer, YesNoAnswer, ChoiceAnswer, TextAnswer, DateTimeAnswer

admin.site.register(Poll)
admin.site.register(EventPlanner)
admin.site.register(Question)
admin.site.register(PollAnswer)
admin.site.register(YesNoAnswer)
admin.site.register(ChoiceAnswer)
admin.site.register(TextAnswer)
admin.site.register(DateTimeAnswer)
