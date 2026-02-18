from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic
from django_htmx.http import HttpResponseClientRefresh, HttpResponseClientRedirect
from cm_main.utils import check_edit_permission, confirm_delete_modal
from ..models import Poll, Question
from ..forms.upsert_forms import PollUpsertForm, QuestionUpsertForm


def managed_closed_list(poll, form):
  if poll.open_to == Poll.OPEN_TO_CLOSED:
    poll.closed_list.set(form.cleaned_data.get("closed_list"))
    poll.save()
  elif poll.closed_list.count() > 0:
    raise ValueError("Closed list must be empty for this type of Poll")


class PollCreateView(generic.CreateView):
  model = Poll
  form_class = PollUpsertForm
  template_name = "polls/poll_upsert_form.html"
  success_message = _("Poll created successfully. You can now add questions.")
  redirect_to = "polls:update_poll"

  def get(self, request):
    form = self.form_class()
    return render(
      request,
      self.template_name,
      {"form": form},
    )

  def post(self, request):
    # create a form instance from the request and save it
    form = self.form_class(request.POST)
    form.instance.owner = request.user
    if form.is_valid():
      poll = form.save()
      managed_closed_list(poll, form)
      messages.success(request, self.success_message)
      return redirect(reverse(self.redirect_to, args=(poll.pk,)))
    else:
      return render(
        request,
        self.template_name,
        {"form": form, "question_form": QuestionUpsertForm()},
      )


class PollUpdateView(generic.UpdateView):
  model = Poll
  form_class = PollUpsertForm
  template_name = "polls/poll_upsert_form.html"
  redirect_to = "polls:poll_detail"
  success_message = _("Poll updated successfully.")

  def form_valid(self, form):
    if form.instance.owner != self.request.user:
      raise ValueError("Only the owner can update this Poll")
    return super().form_valid(form)

  def get(self, request, pk):
    poll = get_object_or_404(self.model, pk=pk)
    form = self.form_class(instance=poll)
    return render(
      request,
      self.template_name,
      {"form": form},
    )

  def post(self, request, pk):
    poll = get_object_or_404(self.model, pk=pk)
    check_edit_permission(request, poll.owner)
    # create a form instance from the request and save it
    form = self.form_class(request.POST, instance=poll)
    if form.is_valid():
      form.save()
      managed_closed_list(poll, form)
      messages.success(request, self.success_message)
      return redirect(reverse(self.redirect_to, args=(poll.pk,)))
    else:
      return render(request, self.template_name, {"form": form})


class PollDeleteView(generic.DeleteView):
  model = Poll

  def get(self, request, pk):
    poll = get_object_or_404(self.model, pk=pk)
    return confirm_delete_modal(
      request,
      _("Delete Poll"),
      _('Are you sure you want to delete the poll "%(title)s"?') % {"title": poll.title},
      expected_value=poll.title,
    )

  def post(self, request, pk):
    poll = get_object_or_404(self.model, pk=pk)
    check_edit_permission(request, poll.owner)
    poll.delete()
    return HttpResponseClientRedirect(reverse("polls:all_polls"))


class QuestionUpsertMixin:
  model = Question
  form_class = QuestionUpsertForm
  template_name = "polls/questions/question_form.html"


class QuestionCreateView(QuestionUpsertMixin, generic.CreateView):
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["poll_id"] = self.kwargs["poll_id"]
    return context

  def post(self, request, poll_id):
    # create a form instance from the request and save it
    form = self.form_class(request.POST)
    poll = get_object_or_404(Poll, pk=poll_id)
    check_edit_permission(request, poll.owner)
    if form.is_valid():
      form.instance.poll = poll
      form.save()
    else:
      messages.error(request, _("Error creating question:%s" % form.errors))
    return HttpResponseClientRefresh()


class QuestionUpdateView(QuestionUpsertMixin, generic.UpdateView):
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["question_id"] = self.kwargs["pk"]
    return context

  # automatic get
  def post(self, request, pk):
    # print("pk", pk)
    question = get_object_or_404(self.model, pk=pk)
    check_edit_permission(request, question.poll.owner)
    # print("Before save", question.__dict__)
    # create a form instance and populate it with data from the request on existing member (or None):
    form = self.form_class(request.POST, instance=question)
    if form.is_valid():
      form.save()
      # print("After save", question.__dict__)
    else:
      messages.error(request, _("Error creating question:%s" % form.errors))
    return HttpResponseClientRefresh()


class QuestionDeleteView(QuestionUpsertMixin, generic.DeleteView):
  model = Question

  def get(self, request, pk):
    question = get_object_or_404(self.model, pk=pk)
    return confirm_delete_modal(
      request,
      _("Delete Question"),
      _('Are you sure you want to delete the question "%(title)s"?') % {"title": question.question_text},
    )

  def post(self, request, pk):
    question = get_object_or_404(self.model, pk=pk)
    check_edit_permission(request, question.poll.owner)
    question.delete()
    return HttpResponseClientRefresh()
