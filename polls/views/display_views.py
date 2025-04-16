from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic

from cousinsmatter.utils import assert_request_is_ajax
from ..models import Poll, Question


class PollsListView(LoginRequiredMixin, generic.ListView):
  "View for listing published Polls."
  model = Poll
  template_name = "polls/polls_list.html"
  context_object_name = "polls_list"
  only_published = True
  ordering = "-pub_date"
  show_closed = False
  only_closed = False
  show_last = 25
  title = _("Open Polls")
  kind = "open"

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

  def get_context_data(self, **kwargs):
      context = super().get_context_data(**kwargs)
      context['title'] = self.title
      context['kind'] = self.kind
      return context


class AllPollsListView(PollsListView):
  "View for listing all Polls."
  only_published = False
  show_closed = True
  show_last = None
  title = _("All Polls")
  kind = "all"


class ClosedPollsListView(PollsListView):
  "View for listing closed Polls."
  only_published = False
  show_closed = True
  only_closed = True
  show_last = None
  ordering = "-close_date"
  title = _("Closed Polls")
  kind = "closed"


class PollDetailView(LoginRequiredMixin, generic.DetailView):
    "View for displaying a Poll, its Questions and the already given Answers."
    model = Poll
    template_name = "polls/poll_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        poll = self.object
        context['poll'] = poll
        context['questions'] = poll.get_results(self.request.user)
        return context


@login_required
def get_question(request, pk):
  # print("get_question", pk)
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
