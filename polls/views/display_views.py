from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic

from cm_main.utils import assert_request_is_ajax
from ..models import EventPlanner, Poll, Question


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
  type = "polls"
  kind = "open"

  def get_queryset(self):
    """
    Returns the list of polls that will be displayed in the list view.

    The filter depends on the class attributes only_published, show_closed and only_closed.
    If only_published is True, only polls with close_date greater than or equal to the current time are included.
    If show_closed is False, only polls with close_date not set or greater than or equal to the current time are included.
    If only_closed is True, only polls with close_date less than or equal to the current time are included.
    The list is ordered by the ordering class attribute, and only the first show_last items are returned.
    """
    filter = Q()
    if self.only_published:
      filter &= Q(pub_date__lte=timezone.now())
    if not self.show_closed:
      filter &= (Q(close_date__gte=timezone.now()) | Q(close_date__isnull=True))
    if self.only_closed:
      filter &= Q(close_date__lte=timezone.now())
    query_set = self.model.objects.filter(filter).order_by(self.ordering)
    result = query_set[:(self.show_last or 250)]
    # print(filter, result, self.__dict__)
    return result

  def get_context_data(self, **kwargs):
      context = super().get_context_data(**kwargs)
      context['title'] = self.title
      context['kind'] = self.kind
      context['tab'] = self.type
      return context


class EventPlannersListView(PollsListView):
  "View for listing published EventPlanners."
  model = EventPlanner
  title = _("Open Event Planners")
  type = "event"


class AllPollsListView(PollsListView):
  "View for listing all Polls."
  only_published = False
  show_closed = True
  show_last = None
  title = _("All Polls")
  kind = "all"


class AllEventPlannersListView(AllPollsListView):
  "View for listing all EventPlanners."
  model = EventPlanner
  title = _("All Event Planners")
  type = "event"


class ClosedPollsListView(PollsListView):
  "View for listing closed Polls."
  only_published = False
  show_closed = True
  only_closed = True
  show_last = None
  ordering = "-close_date"
  title = _("Closed Polls")
  kind = "closed"


class ClosedEventPlannersListView(ClosedPollsListView):
  "View for listing closed EventPlanners."
  model = EventPlanner
  title = _("Closed Event Planners")
  type = "event"


class PollDetailView(LoginRequiredMixin, generic.DetailView):
    "View for displaying a Poll, its Questions and the already given Answers."
    model = Poll
    template_name = "polls/poll_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        poll = self.object
        context['poll'] = poll
        context['questions'] = poll.get_results(self.request.user)
        context['type'] = self.model.__name__.lower()
        return context


class EventPlannerDetailView(PollDetailView):
    "View for displaying an EventPlanner, its Questions and the already given Answers."
    model = EventPlanner


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
