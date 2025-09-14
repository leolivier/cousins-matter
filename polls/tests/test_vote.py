from django.urls import reverse
from django.utils import formats
from django.utils.translation import gettext as _
from .test_base import PollTestMixin
from ..models import Question


class TestVoteView(PollTestMixin):

    def test_vote_view(self):
        "Test that a question can be voted on."
        poll = self.create_poll("Test poll", "Test description")

        questions = self.create_questions(poll)
        self.assertEqual(Question.objects.count(), len(questions))

        response = self.client.get(reverse("polls:vote", args=(poll.id,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.check_display_info(poll, response)
        for question in questions:
            self.assertContains(response, question.question_text)
            self.assertContains(response, f'id="id_q{question.id}-answer')

        self.create_and_check_answers(poll)

    def test_update_vote_view(self):
        """
        Test that a vote can be updated.
        """
        poll = self.create_poll("Test poll", "Test description")

        questions = self.create_questions(poll)
        self.assertEqual(Question.objects.count(), len(questions))
        # 1rst vote, checked in previous test
        qnas = self.create_and_check_answers(poll)
        # now get the 2nd vote screen
        response = self.client.get(reverse("polls:vote", args=(poll.id,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.check_display_info(poll, response)
        for qna in qnas:
            question = qna["question"]
            answer = qna["answer"]
            self.assertContains(response, question.question_text)
            name = f'q{question.id}-answer'
            match question.question_type:
                case Question.YESNO_QUESTION:
                    self.assertContains(response, f'''
<input type="checkbox" name="{name}" aria-describedby="id_{name}_helptext" id="id_{name}" {"checked" if answer else ""}>
''',
                                        html=True)
                case Question.DATE_QUESTION:
                    date = formats.date_format(answer, "SHORT_DATETIME_FORMAT") + ':00'  # need to add seconds manually
                    self.assertContains(response, f'''
<input type="text" required class="datetimeinput input" name="{name}" id="id_{name}" value="{date}">
''',
                                        html=True)
                case Question.OPENTEXT_QUESTION:
                    self.assertContains(response, f'''
<textarea cols="40" rows="10" class="richtextarea" name="{name}" id="id_{name}">{answer}</textarea>
''',
                                        html=True)
                case Question.SINGLECHOICE_QUESTION:
                    select = f'<select name="{name}" aria-describedby="id_{name}_helptext" id="id_{name}">'
                    for choice in question.possible_choices:
                        select += f'<option value="{choice}" {"selected" if answer == choice else ""}>{choice}</option>'
                    self.assertContains(response, select, html=True)
                case Question.MULTICHOICES_QUESTION:
                    select = ''
                    for idx, choice in enumerate(question.possible_choices):
                        select += f'''
<div class="control">
    <label class="checkbox" for="id_{name}_{idx}">
        <input type="checkbox" {"checked" if choice in answer else ""} name="{name}" id="id_{name}_{idx}" value="{choice}">
      {choice}
  </label>
</div>
'''
                    select += f'<p id="id_{name}_helptext" class="help">{_("Select your choices")}</p>'
                    self.assertContains(response, select, html=True)

        # rerun vote with the same questions and the same user but different answers
        self.create_and_check_answers(poll)

    def test_several_votes(self):
        """
        Test that a question can be voted on multiple times by different users.
        """
        poll = self.create_poll("Test poll", "Test description")
        self.create_questions(poll)
        self.create_and_check_answers(poll)
        # rerun vote with the same questions and a different user with different answers
        member = self.create_member(is_active=True)
        self.client.login(username=member.username, password=member.password)
        self.create_and_check_answers(poll, expected_poll_answers=2)
