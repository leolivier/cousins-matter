from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _

from core.htmx import htmx_redirect

from core.utils import check_edit_permission, confirm_delete_modal
from polls.views.upsert_views import (
  PollCreateView,
  PollDeleteView,
  PollUpdateView,
)

from ..forms.upsert_forms import (
  EventPlannerUpsertForm,
  QuestionUpsertForm,
)
from ..models import EventPlanner
from ..services import create_event_planner, update_event_planner, manage_closed_list


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
      possible_choices = form.cleaned_data["possible_dates"]
      if not possible_choices:
        raise ValueError("No possible dates")
      planner = form.save()
      multichoices_planner = form.cleaned_data["multichoices_planner"]
      closed_list = form.cleaned_data.get("closed_list")
      create_event_planner(planner, multichoices_planner, closed_list, possible_choices)

      messages.success(request, self.success_message)
      return redirect(reverse(self.redirect_to, args=(planner.pk,)))
    else:
      return render(
        request,
        self.template_name,
        {"form": form, "question_form": QuestionUpsertForm()},
      )


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
      if not form.cleaned_data["possible_dates"]:
        raise ValueError("No possible dates")
      form.save()
      manage_closed_list(planner, form.cleaned_data.get("closed_list"))
      multichoices_planner = form.cleaned_data["multichoices_planner"]
      (status, message) = update_event_planner(
        planner, multichoices_planner, possible_choices=form.cleaned_data["possible_dates"]
      )
      if status == "error":
        messages.error(request, message)
        return render(request, self.template_name, {"form": form})
      elif status == "warning":
        messages.warning(request, message)
      else:
        messages.success(request, self.success_message)
      return redirect(reverse(self.redirect_to, args=(planner.pk,)))
    else:
      return render(request, self.template_name, {"form": form})


class EventPlannerDeleteView(PollDeleteView):
  model = EventPlanner
  success_url = "/polls/event-planners/all/"

  def get(self, request, pk):
    planner = get_object_or_404(self.model, pk=pk)
    return confirm_delete_modal(
      request,
      _("Delete Event Planner"),
      _('Are you sure you want to delete the event planner "%(title)s"?') % {"title": planner.title},
      expected_value=planner.title,
    )

  def post(self, request, pk):
    planner = get_object_or_404(self.model, pk=pk)
    check_edit_permission(request, planner.owner)
    planner.delete()
    return htmx_redirect(reverse("polls:all_event_planners"))
