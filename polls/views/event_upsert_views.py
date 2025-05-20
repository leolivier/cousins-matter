
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from cm_main.utils import check_edit_permission
from polls.views.upsert_views import PollCreateView, PollDeleteView, PollUpdateView, managed_closed_list
from ..models import Answer, EventPlanner, Question
from ..forms.upsert_forms import QuestionUpsertForm, EventPlannerUpsertForm  # , MultipleEventUpsertForm, PollUpsertForm


class EventPlannerCreateView(PollCreateView):
  model = EventPlanner
  form_class = EventPlannerUpsertForm
  template_name = "polls/planner_upsert_form.html"
  redirect_to = "polls:update_event_planner"
  success_message = _("Event planner created successfully. You can now add other questions if needed.")

  def post(self, request):
    # create a form instance from the request and save it
    form = self.form_class(request.POST)
    form.instance.owner = request.user
    if form.is_valid():
      if not form.cleaned_data['possible_dates']:
        raise ValueError("No possible dates")
      multichoices_planner = form.cleaned_data['multichoices_planner']
      planner = form.save()
      managed_closed_list(planner, form)
      question_text = _("Choose dates") if multichoices_planner else _("Choose one date")
      Question.objects.create(
        question_type=Question.MULTIEVENTPLANNING_QUESTION if multichoices_planner else Question.SINGLEEVENTPLANNING_QUESTION,
        question_text=question_text, poll=planner,
        possible_choices=form.cleaned_data['possible_dates']
      )

      messages.success(request, self.success_message)
      return redirect(reverse(self.redirect_to, args=(planner.pk,)))
    else:
      return render(request, self.template_name, {"form": form, "question_form": QuestionUpsertForm()})


class EventPlannerUpdateView(PollUpdateView):
  model = EventPlanner
  form_class = EventPlannerUpsertForm
  template_name = "polls/planner_upsert_form.html"
  redirect_to = "polls:event_planner_detail"
  success_message = _("Event planner updated successfully.")

  def post(self, request, pk):
    planner = get_object_or_404(self.model, pk=pk)
    check_edit_permission(request, planner.owner)
    # create a form instance from the request and save it
    form = self.form_class(request.POST, instance=planner)
    if form.is_valid():
      if not form.cleaned_data['possible_dates']:
        raise ValueError("No possible dates")
      form.save()
      managed_closed_list(planner, form)
      multichoices_planner = form.cleaned_data['multichoices_planner']
      possible_dates = Question.objects.filter(poll=planner, question_type__in=Question.EVENT_TYPES).first()
      if possible_dates:
        answers = Answer.filter_answers(question=possible_dates)
        if answers:
          if (multichoices_planner and possible_dates.question_type == Question.SINGLEEVENTPLANNING_QUESTION) or \
             (not multichoices_planner and possible_dates.question_type == Question.MULTIEVENTPLANNING_QUESTION):
            messages.error(request, _("This question has already been answered. You can't change its type anymore."))
            return render(request, self.template_name, {"form": form})
          else:
            messages.warning(request, _("This question has already been answered. Previous answers might be ignored."))
        possible_dates.possible_choices = form.cleaned_data['possible_dates']
        possible_dates.question_type = \
          Question.MULTIEVENTPLANNING_QUESTION if multichoices_planner else Question.SINGLEEVENTPLANNING_QUESTION
        if multichoices_planner and possible_dates.question_text == _("Choose one date"):
          possible_dates.question_text = _("Choose dates")
        elif not multichoices_planner and possible_dates.question_text == _("Choose dates"):
          possible_dates.question_text = _("Choose one date")
        possible_dates.save()
      else:
        question_text = _("Choose dates") if multichoices_planner else _("Choose one date")
        Question.objects.create(
          question_type=Question.MULTIEVENTPLANNING_QUESTION if multichoices_planner
                   else Question.SINGLEEVENTPLANNING_QUESTION,  # noqa
          question_text=question_text, poll=planner,
          possible_choices=form.cleaned_data['possible_dates']
        )

      messages.success(request, self.success_message)
      return redirect(reverse(self.redirect_to, args=(planner.pk,)))
    else:
      return render(request, self.template_name, {"form": form})


class EventPlannerDeleteView(PollDeleteView):
  model = EventPlanner
  success_url = "/polls/event-planners/all/"

  def post(self, request, pk):
    planner = get_object_or_404(self.model, pk=pk)
    check_edit_permission(request, planner.owner)
    return super().post(request, pk)