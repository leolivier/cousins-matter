from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic

from ..forms.answer_forms import get_answerform_class_for_question_type
from ..models import Answer, EventPlanner, Poll, PollAnswer
from ..services import get_poll_answer


class PollsVoteView(generic.View):
  model = PollAnswer
  template_name = "polls/poll_vote.html"
  poll_model = Poll
  redirect_to = "polls:poll_detail"

  def get_question_forms(self, poll):
    poll_answer = get_poll_answer(poll, self.request.user)

    return [
      {
        "question": item["question"],
        "form": self.get_question_form_cached(item["answer"], item["question"], item["cache"]),
      }
      for item in poll_answer
    ]

  def get_question_form_cached(self, poll_answer, question, answers_cache):
    """Get question form using cached answers to avoid N+1 queries."""
    form_class = get_answerform_class_for_question_type(question.question_type)
    if poll_answer and question.id in answers_cache:
      return form_class(instance=answers_cache[question.id], prefix=f"q{question.id}")
    return form_class(question=question, prefix=f"q{question.id}")

  def get_question_form_classes(self, questions):
    """Build form classes for given questions (already prefetched)."""
    return [
      {
        "question": question,
        "form": get_answerform_class_for_question_type(question.question_type),
      }
      for question in questions
    ]

  def get(self, request, poll_id):
    poll = get_object_or_404(self.poll_model, pk=poll_id)
    question_forms = self.get_question_forms(poll)
    return render(
      request,
      self.template_name,
      {
        "poll": poll,
        "questions": question_forms,
        "type": self.poll_model.__name__.lower(),
      },
    )

  def post(self, request, poll_id):
    poll = get_object_or_404(self.poll_model, pk=poll_id)

    # Prefetch questions to avoid N+1
    questions = list(poll.questions.all())
    question_form_classes = self.get_question_form_classes(questions)

    # Validate all forms BEFORE touching the database, so that an invalid submission
    # never destroys the member's previous answers.
    question_forms = []
    answers = []
    has_errors = False
    for question_data in question_form_classes:
      question = question_data["question"]
      form = question_data["form"](request.POST, question=question, prefix=f"q{question.id}")
      if form.is_valid():
        answer = form.save(commit=False)
        answer.question = question
        answers.append(answer)
      else:
        has_errors = True
      question_forms.append({"question": question, "form": form})
    if has_errors:
      return render(request, self.template_name, {"poll": poll, "questions": question_forms})

    # are we modifyning an existing answer for that poll and that user?
    poll_answer = PollAnswer.objects.filter(poll=poll, member=request.user)
    if poll_answer.exists():
      poll_answer = poll_answer.first()
    else:
      # otherwise create a new one
      poll_answer = PollAnswer(poll=poll, member=request.user)
      poll_answer.save()

    # Replace the ballot atomically: the delete of the previous answers and the save of
    # the new ones commit together or not at all.
    with transaction.atomic():
      # Delete all previous answers in bulk to avoid N+1 queries
      # Note: We iterate through subclasses because Django's multi-table inheritance
      # requires deleting from each concrete table separately to maintain referential integrity
      Answer.set_subclasses()
      for subclass in Answer.subclasses:
        subclass.objects.filter(poll_answer=poll_answer, question__in=questions).delete()
      for answer in answers:
        answer.poll_answer = poll_answer
        answer.save()
    messages.success(request, _("Your answers have been saved"))
    return redirect(reverse(self.redirect_to, args=(poll.id,)))


class EventPlannersVoteView(PollsVoteView):
  poll_model = EventPlanner
  redirect_to = "polls:event_planner_detail"
