from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import generic

from cousinsmatter.utils import assert_request_is_ajax
from ..models import Poll, Question, Answer
from ..forms.upsert_forms import PollUpsertForm, QuestionUpsertForm


class PollsListView(LoginRequiredMixin, generic.ListView):
  "View for listing published Polls."
  model = Poll
  template_name = "polls/polls_list.html"
  context_object_name = "polls_list"
  only_published = True
  ordering = "-pub_date"
  show_closed = False
  only_closed = False
  show_last = 5

  def get_queryset(self):
    """
    Return the last five published polls (not including those set to be
    published in the future).
    """
    filter = {}
    if self.only_published:
      filter["pub_date__lte"] = timezone.now()
    if not self.show_closed:
      filter["close_date__gte"] = timezone.now()
    if self.only_closed:
      filter["close_date__lte"] = timezone.now()
    query_set = Poll.objects.filter(**filter).order_by(self.ordering)
    result = query_set[:self.show_last] if self.show_last else query_set
    # for poll in result:
    #   print(",".join(m.__str__() for m in poll.closed_list.all()))
    # print(filter, result, self.__dict__)
    return result


class AllPollsListView(PollsListView):
  "View for listing all Polls."
  only_published = False
  show_closed = True
  show_last = None


class ClosedPollsListView(PollsListView):
  "View for listing closed Polls."
  only_published = False
  show_closed = True
  only_closed = True
  show_last = None
  ordering = "-close_date"


class PollDetailView(LoginRequiredMixin, generic.DetailView):
    "View for displaying a Poll, its Questions and the already given Answers."
    model = Poll
    template_name = "polls/poll_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all()
        context['answers'] = Answer.filter_answers(question__poll=self.object)
        return context


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
      messages.success(request, _("Poll created successfully. You can now add questions."))
      return redirect(reverse("polls:update_poll", args=(poll.pk,)))
    else:
      return render(request, self.template_name, {"form": form, "question_form": QuestionUpsertForm(),
                                                  "question_update_form": QuestionUpsertForm(auto_id="updt_id")})


class PollUpdateView(LoginRequiredMixin, generic.UpdateView):
  model = Poll
  form_class = PollUpsertForm
  template_name = "polls/poll_upsert_form.html"

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
    # create a form instance from the request and save it
    form = self.form_class(request.POST, instance=poll)
    if form.is_valid():
      form.save()
      managed_closed_list(poll, form)
      return redirect(reverse("polls:poll_detail", args=(poll.pk,)))
    else:
      return render(request, self.template_name, {"form": form})


class PollDeleteView(LoginRequiredMixin, generic.DeleteView):
  model = Poll
  template_name = "polls/poll_delete.html"
  success_url = "/polls/all/"


class QuestionUpsertViewMixin(LoginRequiredMixin):
  model = Question
  form_class = QuestionUpsertForm
  template_name = "cm_main/common/modal_form.html"


class QuestionCreateView(QuestionUpsertViewMixin, generic.CreateView):
  def post(self, request, poll_id):
    # create a form instance from the request and save it
    form = self.form_class(request.POST)
    if form.is_valid():
      form.instance.poll_id = poll_id
      form.save()
      return redirect(reverse("polls:update_poll", args=(poll_id,)))
    else:
      return render(request, self.template_name, {"form": form})


class QuestionUpdateView(QuestionUpsertViewMixin, generic.UpdateView):
  def post(self, request, poll_id, pk):
    print("poll_id", poll_id, "pk", pk)
    question = get_object_or_404(self.model, pk=pk)
    print("Before save", question.__dict__)
    if question.poll.id != poll_id:
      raise ValueError('Question does not belong to this Poll')
    # create a form instance and populate it with data from the request on existing member (or None):
    form = self.form_class(request.POST, instance=question)
    if form.is_valid():
      question = form.save()
      print("After save", question.__dict__)
      return redirect(reverse("polls:update_poll", args=(poll_id,)))
    else:
      return render(request, self.template_name, {"form": form})


@login_required
def get_question(request, pk):
  print("get_question", pk)
  assert_request_is_ajax(request)
  if request.method != 'GET':
    return JsonResponse({"error": "Only GET method is allowed"}, status=405)
  question = get_object_or_404(Question, pk=pk)
  # print("returning question", question.question_text)
  return JsonResponse({'question_id': question.id,
                       'question_text': question.question_text,
                       'question_type': question.question_type,
                       'possible_choices': '\n'.join(question.possible_choices)
                       }, status=200)
