from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic
from cm_main.utils import check_edit_permission
from ..models import Poll, Question
from ..forms.upsert_forms import PollUpsertForm, QuestionUpsertForm


def managed_closed_list(poll, form):
  if poll.open_to == Poll.OPEN_TO_CLOSED:
    poll.closed_list.set(form.cleaned_data.get('closed_list'))
    poll.save()
  elif poll.closed_list.count() > 0:
    raise ValueError('Closed list must be empty for this type of Poll')


class PollCreateView(LoginRequiredMixin, generic.CreateView):
  model = Poll
  form_class = PollUpsertForm
  template_name = "polls/poll_upsert_form.html"
  success_message = _("Poll created successfully. You can now add questions.")
  redirect_to = "polls:update_poll"

  def get(self, request):
    form = self.form_class()
    return render(request, self.template_name, {"form": form, "question_form": QuestionUpsertForm()})

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
      return render(request, self.template_name, {"form": form, "question_form": QuestionUpsertForm()})


class PollUpdateView(LoginRequiredMixin, generic.UpdateView):
  model = Poll
  form_class = PollUpsertForm
  template_name = "polls/poll_upsert_form.html"
  redirect_to = "polls:poll_detail"
  success_message = _("Poll updated successfully.")

  def form_valid(self, form):
    if form.instance.owner != self.request.user:
      raise ValueError('Only the owner can update this Poll')
    return super().form_valid(form)

  def get(self, request, pk):
    poll = get_object_or_404(self.model, pk=pk)
    form = self.form_class(instance=poll)
    return render(request, self.template_name, {"form": form, "question_form": QuestionUpsertForm()})

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


class PollDeleteView(LoginRequiredMixin, generic.DeleteView):
  model = Poll
  success_url = "/polls/all/"

  def post(self, request, pk):
    check_edit_permission(request, self.get_object().owner)
    return super().post(request, pk)


class QuestionUpsertViewMixin(LoginRequiredMixin):
  model = Question
  form_class = QuestionUpsertForm
  template_name = "cm_main/common/modal_form.html"


class QuestionCreateView(QuestionUpsertViewMixin, generic.CreateView):
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
    return redirect(reverse("polls:update_poll", args=(poll_id,)))


class QuestionUpdateView(QuestionUpsertViewMixin, generic.UpdateView):
  def post(self, request, poll_id, pk):
    # print("poll_id", poll_id, "pk", pk)
    question = get_object_or_404(self.model, pk=pk)
    check_edit_permission(request, question.poll.owner)
    # print("Before save", question.__dict__)
    if question.poll.id != poll_id:
      raise ValueError('Question does not belong to this Poll')
    # create a form instance and populate it with data from the request on existing member (or None):
    form = self.form_class(request.POST, instance=question)
    if form.is_valid():
      form.save()
      # print("After save", question.__dict__)
    else:
      messages.error(request, _("Error creating question:%s" % form.errors))
    return redirect(reverse("polls:update_poll", args=(poll_id,)))


class QuestionDeleteView(QuestionUpsertViewMixin, generic.DeleteView):
  model = Question

  def post(self, request, pk):
    question = get_object_or_404(self.model, pk=pk)
    check_edit_permission(request, question.poll.owner)
    poll_id = question.poll.id
    question.delete()
    return redirect(reverse("polls:update_poll", args=(poll_id,)))
