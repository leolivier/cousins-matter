import datetime
import random
import string
from django.urls import reverse
from django.utils import timezone, formats

from members.tests.tests_member_base import MemberTestCase
from ..models import Question, Poll, PollAnswer, Answer

random.seed()


class PollTestMixin(MemberTestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()
        Poll.objects.all().delete()
        self.assertEqual(Question.objects.count(), 0)  # check delete cascade

    def set_dates(self, pub_days=0, duration=1):
        self.pub_date = timezone.now() + datetime.timedelta(days=pub_days)
        self.close_date = self.pub_date + datetime.timedelta(days=duration)

    def create_poll(self, title, description, open_to=Poll.OPEN_TO_ACTIVE, pub_days=-1, duration=2):
        """
        Create a poll with the given `title` and `description` and published the
        given number of `days` offset to now (negative for polls published
        in the past, positive for polls that have yet to be published) and closed in
        `duration` days after the publication date.
        """
        self.set_dates(pub_days, duration)
        poll = Poll(title=title, description=description,
                    pub_date=self.pub_date, close_date=self.close_date,
                    open_to=open_to, owner=self.member)
        poll.save()
        self.assertEqual(Poll.objects.get(pk=poll.id), poll)
        return poll

    def create_question(self, poll, question_text, question_type, possible_choices=None):
        """
        Create a question with the given `question_text` and `question_type`.
        The question is added to the given `poll`. For multiple choice questions,
        `choices` is a list of choices.
        """
        question = Question(question_text=question_text, question_type=question_type,
                            poll=poll, possible_choices=possible_choices or [])
        question.save()
        return question

    def check_display_info(self, poll, response):
        self.assertContains(response, poll.title)
        self.assertContains(response, poll.description)
        self.assertContains(response, poll.owner.full_name)
        time = timezone.localtime(poll.pub_date)
        self.assertContains(response, formats.date_format(time, "SHORT_DATETIME_FORMAT"))
        time = timezone.localtime(poll.close_date)
        self.assertContains(response, formats.date_format(time, "SHORT_DATETIME_FORMAT"))
        time = timezone.localtime(poll.created_at)
        self.assertContains(response, formats.date_format(time, "SHORT_DATETIME_FORMAT"))
        self.assertContains(response, poll.get_open_to_display())
        if poll.open_to == "lst":
            for m in poll.closed_list.all():
                self.assertContains(response, m)

    def create_questions(self, poll):
        rnd_str = ''.join(random.choice(string.ascii_letters) for _ in range(10))
        possible_choices = ["Choice #1", "Choice #2", "Choice #3"]

        return [
            self.create_question(question_text=f"Test question 1 {rnd_str}",
                                 question_type=Question.YESNO_QUESTION, poll=poll),
            self.create_question(question_text=f"Test question 2 {rnd_str}",
                                 question_type=Question.DATE_QUESTION, poll=poll),
            self.create_question(question_text=f"Test question 3 {rnd_str}",
                                 question_type=Question.MULTICHOICES_QUESTION,
                                 poll=poll, possible_choices=possible_choices),
            self.create_question(question_text=f"Test question 4 {rnd_str}",
                                 question_type=Question.OPENTEXT_QUESTION, poll=poll),
        ]

    def create_qnas(self, questions):
        rnd_str = ''.join(random.choice(string.ascii_letters) for _ in range(10))
        rnd_date = timezone.localtime(timezone.make_aware(datetime.datetime(
            random.randint(2020, 2025),
            random.randint(1, 12),
            random.randint(1, 28),
            random.randint(0, 23),
            random.randint(0, 59))))
        rnd_bool = (random.randint(0, 1) == 1)
        return [
            {
                "question": questions[0],
                "answer": rnd_bool,
            },
            {
                "question": questions[1],
                "answer": rnd_date,
            },
            {
                "question": questions[2],
                "answer": random.choice(questions[2].possible_choices),
            },
            {
                "question": questions[3],
                "answer": f"Test answer {rnd_str}",
            },
        ]

    def create_and_check_answers(self, poll, expected_poll_answers=1):
        questions = poll.questions.all()
        qnas = self.create_qnas(questions)
        response = self.client.post(
            reverse("polls:vote", args=(poll.id,)),
            {f"q{qna['question'].id}-answer": qna["answer"] for qna in qnas},
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PollAnswer.objects.count(), expected_poll_answers)
        poll_answer = PollAnswer.objects.filter(poll=poll, member=self.current_member()).first()

        answers = Answer.filter_answers(poll_answer=poll_answer)
        self.assertEqual(len(answers), len(qnas))

        for answer in answers:
            question_found = False
            for qna in qnas:
                if answer.question.id == qna["question"].id:
                    self.assertEqual(answer.answer, qna["answer"])
                    question_found = True
                    break
            self.assertTrue(question_found)

        return qnas
