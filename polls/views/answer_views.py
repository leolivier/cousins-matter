from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic

from ..models import Answer, PollAnswer, Poll, Question
from ..forms.answer_forms import get_answerform_class_for_question_type


class PollsVoteView(LoginRequiredMixin, generic.View):
    model = PollAnswer
    template_name = "polls/poll_vote.html"

    def get_question_form(self, question):
      form_class = get_answerform_class_for_question_type(question.question_type)
      return form_class(question=question)

    def get_question_forms(self, poll):
      return [{"question": question, "form": self.get_question_form(question)}
              for question in poll.questions.all()]

    def get_question_form_classes(self, poll):
      return [{"question": question, "form": get_answerform_class_for_question_type(question.question_type)}
              for question in poll.questions.all()]

    def get(self, request, poll_id):
      poll = get_object_or_404(Poll, pk=poll_id)
      question_forms = self.get_question_forms(poll)
      return render(request, self.template_name, {"poll": poll, 'questions': question_forms})

    def post(self, request, poll_id):
      poll = get_object_or_404(Poll, pk=poll_id)
      question_form_classes = self.get_question_form_classes(poll)
      # are we modifyning an existing answer for that poll and that user?
      poll_answer = PollAnswer.objects.filter(poll=poll, member=request.user)
      if poll_answer.exists():
        poll_answer = poll_answer.first()
      else:
        # otherwise create a new one
        poll_answer = PollAnswer(poll=poll, member=request.user)
        poll_answer.save()

      for question_data in question_form_classes:
        question = question_data["question"]
        form_class = question_data["form"]
        # delete all answers for this question and this user
        Answer.filter_answers(poll_answer=poll_answer, question=question).delete()
        form = form_class(request.POST, question=question)
        if form.is_valid():
          answer = form.save(commit=False)
          answer.question = question
          answer.poll_answer = poll_answer
          answer.save()
      return redirect(reverse("polls:results", args=(poll.id, )))


class PollResultsView(LoginRequiredMixin, generic.DetailView):
    model = Question
    template_name = "polls/poll_results.html"

    def get(self, request, poll_id):
      poll_answer = get_object_or_404(PollAnswer, poll__id=poll_id, member=request.user)
      return render(request, self.template_name, {"poll_answer": poll_answer})


# @login_required
# def vote(request, question_id):
#   question = get_object_or_404(Question, pk=question_id)
#   try:
#     selected_choice = question.choices.get(pk=request.POST["choice"])
#   except (KeyError, Choice.DoesNotExist):
#     # send error message to user
#     messages.error(request, _("You didn't select a choice."))
#     # Redisplay the question voting form.
#     return render(request, "polls/poll_vote.html", {"question": question})
#   else:
#     selected_choice.votes += 1
#     selected_choice.save()
#     return redirect(reverse("polls:poll_results", args=(question.id, )))
