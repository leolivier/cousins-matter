from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import Poll, PollAnswer, Answer, Question


def get_filtered_polls(model, only_published: bool, show_closed: bool, only_closed: bool, ordering: str = ""):
  filter = Q()
  if only_published:
    filter &= Q(pub_date__lte=timezone.now())
  if not show_closed:
    filter &= Q(close_date__gte=timezone.now()) | Q(close_date__isnull=True)
  if only_closed:
    filter &= Q(close_date__lte=timezone.now())
  if model == Poll:  # Exclude EventPlanners
    filter &= Q(eventplanner__isnull=True)
  return model.objects.filter(filter).select_related("owner").order_by(ordering)


def get_poll_answer(poll, user):
  # is there an existing answer for that poll and that user?
  poll_answer = PollAnswer.objects.filter(poll=poll, member=user).first()

  # Prefetch all questions to avoid N+1
  questions = poll.questions.all()

  # Prefetch all existing answers if poll_answer exists to avoid N+1 queries
  if poll_answer:
    Answer.set_subclasses()
    # Build a cache of existing answers by question_id
    answers_cache = {}
    for subclass in Answer.subclasses:
      for answer in subclass.objects.filter(poll_answer=poll_answer, question__in=questions):
        answers_cache[answer.question_id] = answer
  else:
    answers_cache = {}

  return [
    {
      "question": question,
      "answer": poll_answer,
      "cache": answers_cache,
    }
    for question in questions
  ]


def manage_closed_list(poll, closed_list):
  if poll.open_to == Poll.OPEN_TO_CLOSED:
    poll.closed_list.set(closed_list)
    poll.save()
  elif poll.closed_list.count() > 0:
    raise ValueError("Closed list must be empty for this type of Poll")


def create_event_planner(planner, multichoices_planner, closed_list, possible_choices):
  manage_closed_list(planner, closed_list)
  question_text = _("Choose dates") if multichoices_planner else _("Choose one date")
  Question.objects.create(
    question_type=Question.MULTIEVENTPLANNING_QUESTION if multichoices_planner else Question.SINGLEEVENTPLANNING_QUESTION,
    question_text=question_text,
    poll=planner,
    possible_choices=possible_choices,
  )


def update_event_planner(planner, multichoices_planner, possible_choices):
  possible_dates = Question.objects.filter(poll=planner, question_type__in=Question.EVENT_TYPES).first()
  result = (None, None)
  if possible_dates:
    # Use the specific answer class based on question type to avoid iterating all subclasses
    answer_class = Answer.get_answer_class_for_question_type(possible_dates.question_type)
    answers = answer_class.objects.filter(question=possible_dates)
    if answers.exists():
      if (multichoices_planner and possible_dates.question_type == Question.SINGLEEVENTPLANNING_QUESTION) or (
        not multichoices_planner and possible_dates.question_type == Question.MULTIEVENTPLANNING_QUESTION
      ):
        return (
          "error",
          _("This question has already been answered. You can't change its type anymore."),
        )
      else:
        result = (
          "warning",
          _("This question has already been answered. Previous answers might be ignored."),
        )
    possible_dates.possible_choices = possible_choices
    possible_dates.question_type = (
      Question.MULTIEVENTPLANNING_QUESTION if multichoices_planner else Question.SINGLEEVENTPLANNING_QUESTION
    )
    if multichoices_planner and possible_dates.question_text == _("Choose one date"):
      possible_dates.question_text = _("Choose dates")
    elif not multichoices_planner and possible_dates.question_text == _("Choose dates"):
      possible_dates.question_text = _("Choose one date")
    possible_dates.save()
  else:
    question_text = _("Choose dates") if multichoices_planner else _("Choose one date")
    Question.objects.create(
      question_type=Question.MULTIEVENTPLANNING_QUESTION if multichoices_planner else Question.SINGLEEVENTPLANNING_QUESTION,  # noqa
      question_text=question_text,
      poll=planner,
      possible_choices=possible_choices,
    )
    # success message managed by the caller
  return result
