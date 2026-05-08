from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic

from ..forms.answer_forms import get_answerform_class_for_question_type
from ..models import Answer, EventPlanner, Poll, PollAnswer


class PollsVoteView(generic.View):
  model = PollAnswer
  template_name = "polls/poll_vote.html"
  poll_model = Poll
  redirect_to = "polls:poll_detail"

  def get_question_form(self, poll_answer, question):
    form_class = get_answerform_class_for_question_type(question.question_type)
    # is there an existing answer for that poll question and that user?
    if poll_answer:
      answer = Answer.filter_answers(poll_answer=poll_answer, question=question)
      if answer:
        return form_class(instance=answer[0], prefix=f"q{question.id}")
    return form_class(question=question, prefix=f"q{question.id}")

  def get_question_forms(self, poll):
    # is there an existing answer for that poll and that user?
    poll_answer = PollAnswer.objects.filter(poll=poll, member=self.request.user).first()

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
        "form": self.get_question_form_cached(poll_answer, question, answers_cache),
      }
      for question in questions
    ]

  def get_question_form_cached(self, poll_answer, question, answers_cache):
    """Get question form using cached answers to avoid N+1 queries."""
    form_class = get_answerform_class_for_question_type(question.question_type)
    if poll_answer and question.id in answers_cache:
      return form_class(instance=answers_cache[question.id], prefix=f"q{question.id}")
    return form_class(question=question, prefix=f"q{question.id}")

  def get_question_form_classes(self, poll):
    return [
      {
        "question": question,
        "form": get_answerform_class_for_question_type(question.question_type),
      }
      for question in poll.questions.all()
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
    question_form_classes = [
      {
        "question": question,
        "form": get_answerform_class_for_question_type(question.question_type),
      }
      for question in questions
    ]

    # are we modifyning an existing answer for that poll and that user?
    poll_answer = PollAnswer.objects.filter(poll=poll, member=request.user)
    if poll_answer.exists():
      poll_answer = poll_answer.first()
    else:
      # otherwise create a new one
      poll_answer = PollAnswer(poll=poll, member=request.user)
      poll_answer.save()

    # Delete all previous answers in bulk to avoid N+1 queries
    Answer.set_subclasses()
    for subclass in Answer.subclasses:
      subclass.objects.filter(poll_answer=poll_answer, question__in=questions).delete()

    has_errors = False
    question_forms = []
    for question_data in question_form_classes:
      question = question_data["question"]
      form_class = question_data["form"]
      form = form_class(request.POST, question=question, prefix=f"q{question.id}")
      if form.is_valid():
        answer = form.save(commit=False)
        answer.question = question
        answer.poll_answer = poll_answer
        answer.save()
      else:
        has_errors = True
      question_forms.append({"question": question, "form": form})
    if has_errors:
      return render(request, self.template_name, {"poll": poll, "questions": question_forms})
    messages.success(request, _("Your answers have been saved"))
    return redirect(reverse(self.redirect_to, args=(poll.id,)))


class EventPlannersVoteView(PollsVoteView):
  poll_model = EventPlanner
  redirect_to = "polls:event_planner_detail"
