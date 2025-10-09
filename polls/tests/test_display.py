from django.urls import reverse
from django.utils import formats, timezone

from cm_main.templatetags.cm_tags import icon
from polls.templatetags.polls_tags import question_icon
from .test_base import PollTestMixin
from ..models import Answer, Poll, PollAnswer, Question


class TestDisplayPollInfo(PollTestMixin):
    def test_display_poll_info(self):
        """
        Test that poll information is displayed correctly, including title, description,
        owner, publication date, close date, and open to status, along with any questions
        and answers if they exist.
        """

        poll = self.create_poll("Test poll", "Test description")
        questions = self.create_questions(poll)
        # create answers by 2 users
        self.create_and_check_answers(poll)
        member = self.create_member(is_active=True)
        self.client.login(username=member.username, password=member.password)
        self.create_and_check_answers(poll, expected_poll_answers=2)

        response = self.client.get(reverse("polls:poll_detail", args=(poll.id,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.check_display_info(poll, response)
        poll_answer = PollAnswer.objects.filter(poll=poll, member=self.current_user()).first()
        for question in questions:
            answers = Answer.filter_answers(question=question)
            answer = next((a for a in answers if a.poll_answer == poll_answer), None)
            match question.question_type:
                case Question.YESNO_QUESTION:
                    result = sum(1 for a in answers if a.answer)/len(answers)
                    result = f"{result:.1%}"
                case Question.DATE_QUESTION:
                    result = "<br><hr>".join([formats.date_format(timezone.localtime(a.answer), "DATETIME_FORMAT")
                                              for a in answers])
                case Question.OPENTEXT_QUESTION:
                    result = "<br><hr>".join((a.answer for a in answers))
                case Question.SINGLECHOICE_QUESTION:
                    choice_results = {}
                    for choice in question.possible_choices:
                        choice_results[choice] = sum(1 for a in answers if a.answer == choice)/len(answers)
                    result = '<br><hr>'.join([f"{choice}: {choice_results[choice]:.1%}"
                                              for choice in question.possible_choices])
                case Question.MULTICHOICES_QUESTION:
                    choice_results = {}
                    for choice in question.possible_choices:
                        choice_results[choice] = sum(1 for a in answers if choice in a.answer)/len(answers)
                    result = '<br><hr>'.join([f"{choice}: {choice_results[choice]:.1%}"
                                              for choice in question.possible_choices])

            line = f"""
<div class="cell has-text-centered my-auto has-background-link has-text-light is-col-span-3">
  {icon(question_icon(question.question_type))}
  {question.question_text}
</div>
<div class="cell has-text-centered my-auto">{len(answers)}</div>
<div class="cell has-text-centered my-auto is-col-span-2">{str(answer)}</div>
<div class="cell has-text-centered my-auto is-col-span-2">{result}<br><hr></div>
"""
            self.assertContains(response, line, html=True)

    def test_display_poll_no_question_info(self):
        """
        Test that the poll info is displayed even if there are no questions.
        """
        poll = self.create_poll("Test poll", "Test description")

        response = self.client.get(reverse("polls:poll_detail", args=(poll.id,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.check_display_info(poll, response)

    def test_display_poll_no_answers_info(self):
        """
        Test that the poll info is displayed even if there are no questions.
        """
        poll = self.create_poll("Test poll", "Test description")
        questions = self.create_questions(poll)

        response = self.client.get(reverse("polls:poll_detail", args=(poll.id,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.check_display_info(poll, response)

        for question in questions:
            match question.question_type:
                case Question.YESNO_QUESTION:
                    result = "0%"
                case Question.DATE_QUESTION:
                    result = "-"
                case Question.OPENTEXT_QUESTION:
                    result = '-'
                case Question.SINGLECHOICE_QUESTION:
                    result = '<br><hr>'.join([f"{choice}: 0%" for choice in question.possible_choices])
                case Question.MULTICHOICES_QUESTION:
                    result = '<br><hr>'.join([f"{choice}: 0%" for choice in question.possible_choices])
            line = f"""
<div class="cell has-text-centered my-auto has-background-link has-text-light is-col-span-3">
  {icon(question_icon(question.question_type))}
  {question.question_text}
</div>
<div class="cell has-text-centered my-auto">0</div>
<div class="cell has-text-centered my-auto is-col-span-2">-</div>
<div class="cell has-text-centered my-auto is-col-span-2">{result}<br><hr></div>
"""
            self.assertContains(response, line, html=True)


class TestPollListsView(PollTestMixin):
    def setUp(self):
        super().setUp()
        self.create_poll("published, not yet closed", "Test poll 1",
                         pub_days=-1, duration=2)
        self.create_poll("published today, not yet closed", "Test poll 2",
                         pub_days=0, duration=2)
        self.create_poll("not published yet, not yet closed", "Test poll 3",
                         pub_days=1, duration=2)
        self.create_poll("published and closed", "Test poll 4",
                         pub_days=-5, duration=2)

    def tearDown(self):
        Poll.objects.all().delete()
        return super().tearDown()

    def test_display_polls_list(self):
        response = self.client.get(reverse("polls:list_polls"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "polls/polls_list.html")
        self.assertNotContains(response, "not published yet, not yet closed")
        self.assertContains(response, "published, not yet closed")
        self.assertContains(response, "published today, not yet closed")
        self.assertNotContains(response, "published and closed")

    def test_display_all_polls(self):
        response = self.client.get(reverse("polls:all_polls"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "polls/polls_list.html")
        self.assertContains(response, "not published yet, not yet closed")
        self.assertContains(response, "published, not yet closed")
        self.assertContains(response, "published today, not yet closed")
        self.assertContains(response, "published and closed")

    def test_display_closed_polls(self):
        response = self.client.get(reverse("polls:closed_polls"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "polls/polls_list.html")
        self.assertNotContains(response, "not published yet, not yet closed")
        self.assertNotContains(response, "published, not yet closed")
        self.assertNotContains(response, "published today, not yet closed")
        self.assertContains(response, "published and closed")
