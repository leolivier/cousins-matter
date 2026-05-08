from django.contrib import admin

from .models import (
  ChoiceAnswer,
  DateTimeAnswer,
  EventPlanner,
  MultiChoiceAnswer,
  MultiEventAnswer,
  Poll,
  PollAnswer,
  Question,
  SingleEventAnswer,
  TextAnswer,
  YesNoAnswer,
)


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
  list_display = ["title", "owner", "pub_date", "close_date", "open_to"]
  list_select_related = ["owner"]
  filter_horizontal = ["closed_list"]
  search_fields = ["title", "description"]
  list_filter = ["open_to", "pub_date", "close_date"]


@admin.register(EventPlanner)
class EventPlannerAdmin(admin.ModelAdmin):
  list_display = ["title", "owner", "location", "chosen_date", "pub_date"]
  list_select_related = ["owner"]
  filter_horizontal = ["closed_list"]
  search_fields = ["title", "description", "location"]
  list_filter = ["pub_date", "close_date"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
  list_display = ["question_text", "poll", "question_type"]
  list_select_related = ["poll"]
  search_fields = ["question_text"]
  list_filter = ["question_type"]


@admin.register(PollAnswer)
class PollAnswerAdmin(admin.ModelAdmin):
  list_display = ["poll", "member"]
  list_select_related = ["poll", "member"]
  search_fields = ["poll__title", "member__user__username"]


# Base admin class for all Answer types
class AnswerAdmin(admin.ModelAdmin):
  list_select_related = ["poll_answer", "question", "poll_answer__poll", "poll_answer__member"]
  list_display = ["get_poll", "get_member", "question", "answer"]
  search_fields = ["question__question_text", "poll_answer__member__user__username"]

  def get_poll(self, obj):
    return obj.poll_answer.poll.title

  get_poll.short_description = "Poll"
  get_poll.admin_order_field = "poll_answer__poll"

  def get_member(self, obj):
    return obj.poll_answer.member

  get_member.short_description = "Member"
  get_member.admin_order_field = "poll_answer__member"


admin.site.register(YesNoAnswer, AnswerAdmin)
admin.site.register(ChoiceAnswer, AnswerAdmin)
admin.site.register(TextAnswer, AnswerAdmin)
admin.site.register(DateTimeAnswer, AnswerAdmin)
admin.site.register(SingleEventAnswer, AnswerAdmin)
admin.site.register(MultiChoiceAnswer, AnswerAdmin)
admin.site.register(MultiEventAnswer, AnswerAdmin)
