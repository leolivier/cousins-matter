from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic

from ..models import Answer, EventPlanner, PollAnswer, Poll
from ..forms.answer_forms import get_answerform_class_for_question_type


class PollsVoteView(LoginRequiredMixin, generic.View):
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
        poll_answer = PollAnswer.objects.filter(
            poll=poll, member=self.request.user
        ).first()
        return [
            {
                "question": question,
                "form": self.get_question_form(poll_answer, question),
            }
            for question in poll.questions.all()
        ]

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
        question_form_classes = self.get_question_form_classes(poll)
        # are we modifyning an existing answer for that poll and that user?
        poll_answer = PollAnswer.objects.filter(poll=poll, member=request.user)
        if poll_answer.exists():
            poll_answer = poll_answer.first()
        else:
            # otherwise create a new one
            poll_answer = PollAnswer(poll=poll, member=request.user)
            poll_answer.save()
        has_errors = False
        question_forms = []
        for question_data in question_form_classes:
            question = question_data["question"]
            form_class = question_data["form"]
            # delete all answers for this question and this user
            previous_answers = Answer.filter_answers(
                poll_answer=poll_answer, question=question
            )
            if previous_answers:
                previous_answers[0].delete()
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
            return render(
                request, self.template_name, {"poll": poll, "questions": question_forms}
            )
        messages.success(request, _("Your answers have been saved"))
        return redirect(reverse(self.redirect_to, args=(poll.id,)))


class EventPlannersVoteView(PollsVoteView):
  poll_model = EventPlanner
  redirect_to = "polls:event_planner_detail"
