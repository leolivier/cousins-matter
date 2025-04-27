import datetime
from django.urls import reverse
from .test_base import PollTestMixin
from ..models import Poll, Question


class PollUpsertTest(PollTestMixin):
    def test_create_poll_view(self):
        response = self.client.get(reverse("polls:create_poll"))
        self.assertEqual(response.status_code, 200)
        self.set_dates(pub_days=-1, duration=2)
        response = self.client.post(
            reverse("polls:create_poll"),
            {
                "title": "Test poll",
                "description": "Test description",
                "pub_date": self.pub_date.isoformat(),
                "close_date": self.close_date.isoformat(),
                "open_to": Poll.OPEN_TO_ACTIVE,
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Poll.objects.count(), 1)

        poll = Poll.objects.first()
        self.assertEqual(poll.title, "Test poll")
        self.assertEqual(poll.description, "Test description")
        self.assertEqual(poll.pub_date, self.pub_date)
        self.assertEqual(poll.close_date, self.close_date)
        self.assertEqual(poll.open_to, Poll.OPEN_TO_ACTIVE)

    def test_update_poll_view(self):
        poll = self.create_poll("Test poll", "Test description")
        response = self.client.get(reverse("polls:update_poll", args=(poll.id,)))
        self.assertEqual(response.status_code, 200)
        pub_date = self.pub_date + datetime.timedelta(days=1)
        close_date = self.close_date + datetime.timedelta(days=1)
        response = self.client.post(
            reverse("polls:update_poll", args=(poll.id,)),
            {
                "title": "Updated poll",
                "description": "Updated description",
                "pub_date": pub_date.isoformat(),
                "close_date": close_date.isoformat(),
                "open_to": Poll.OPEN_TO_ALL,
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Poll.objects.count(), 1)

        poll = Poll.objects.first()
        self.assertEqual(poll.title, "Updated poll")
        self.assertEqual(poll.description, "Updated description")
        self.assertEqual(poll.pub_date, pub_date)
        self.assertEqual(poll.close_date, close_date)
        self.assertEqual(poll.open_to, Poll.OPEN_TO_ALL)


class PollDeleteViewTest(PollTestMixin):
    def test_delete_poll_view(self):
        poll = self.create_poll("Test poll", "Test description")
        self.create_question(question_text="Test question", question_type=Question.YESNO_QUESTION, poll=poll)

        response = self.client.post(reverse("polls:delete_poll", args=(poll.id,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Poll.objects.count(), 0)
        self.assertEqual(Question.objects.count(), 0)


class QuestionUpsertTest(PollTestMixin):
    def test_create_questions_view(self):
        """
        Test that a question can be added to a poll.
        """
        poll = self.create_poll("Test poll", "Test description")

        response = self.client.post(
            reverse("polls:add_question", args=(poll.id,)),
            {
                "question_text": "Test MC question",
                "question_type": Question.SINGLECHOICE_QUESTION,
                "possible_choices": "Choice 1\nChoice 2",
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 1)

        question = Question.objects.first()
        self.assertEqual(question.question_text, "Test MC question")
        self.assertEqual(question.question_type, Question.SINGLECHOICE_QUESTION)
        self.assertSequenceEqual(question.possible_choices, ["Choice 1", "Choice 2"])

        response = self.client.post(
            reverse("polls:add_question", args=(poll.id,)),
            {
                "question_text": "Test YN question",
                "question_type": Question.YESNO_QUESTION,
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 2)

        question = Question.objects.last()
        self.assertEqual(question.question_text, "Test YN question")
        self.assertEqual(question.question_type, Question.YESNO_QUESTION)

        response = self.client.post(
            reverse("polls:add_question", args=(poll.id,)),
            {
                "question_text": "Test OT question",
                "question_type": Question.OPENTEXT_QUESTION,
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 3)

        question = Question.objects.last()
        self.assertEqual(question.question_text, "Test OT question")
        self.assertEqual(question.question_type, Question.OPENTEXT_QUESTION)

        response = self.client.post(
            reverse("polls:add_question", args=(poll.id,)),
            {
                "question_text": "Test DT question",
                "question_type": Question.DATE_QUESTION,
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 4)

        question = Question.objects.last()
        self.assertEqual(question.question_text, "Test DT question")
        self.assertEqual(question.question_type, Question.DATE_QUESTION)

        response = self.client.post(
            reverse("polls:add_question", args=(poll.id,)),
            {
                "question_text": "Test MC question",
                "question_type": Question.MULTICHOICES_QUESTION,
                "possible_choices": "Choice #1\nChoice #2\nChoice #3\nChoice #4",
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 5)

        question = Question.objects.last()
        self.assertEqual(question.question_text, "Test MC question")
        self.assertEqual(question.question_type, Question.MULTICHOICES_QUESTION)
        self.assertSequenceEqual(question.possible_choices, ["Choice #1", "Choice #2", "Choice #3", "Choice #4"])

    def test_update_questions_view(self):
        """
        Test that a question's type can be changed.
        """
        poll = self.create_poll("Test poll", "Test description")
        question = self.create_question(question_text="Test YN question", question_type=Question.YESNO_QUESTION,
                                        poll=poll)

        response = self.client.post(
            reverse("polls:update_question", args=(poll.id, question.id,)),
            {
                "question_text": "Updated YN question",
                "question_type": Question.YESNO_QUESTION,
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 1)

        question = Question.objects.first()
        self.assertEqual(question.question_text, "Updated YN question")
        self.assertEqual(question.question_type, Question.YESNO_QUESTION)

        question = self.create_question(question_text="Test SC question", question_type=Question.SINGLECHOICE_QUESTION,
                                        poll=poll, possible_choices=["Choice 1", "Choice 2"])

        response = self.client.post(
            reverse("polls:update_question", args=(poll.id, question.id,)),
            {
                "question_text": "Updated SC question",
                "question_type": Question.SINGLECHOICE_QUESTION,
                "possible_choices": "Choice 1\nChoice 2\nChoice 3",
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 2)

        question = Question.objects.last()
        self.assertEqual(question.question_text, "Updated SC question")
        self.assertEqual(question.question_type, Question.SINGLECHOICE_QUESTION)
        self.assertSequenceEqual(question.possible_choices, ["Choice 1", "Choice 2", "Choice 3"])

        question = self.create_question(question_text="Test MC question", question_type=Question.MULTICHOICES_QUESTION,
                                        poll=poll, possible_choices=["Choice 1", "Choice 2"])

        response = self.client.post(
            reverse("polls:update_question", args=(poll.id, question.id,)),
            {
                "question_text": "Updated MC question",
                "question_type": Question.MULTICHOICES_QUESTION,
                "possible_choices": "Choice 1\nChoice 2\nChoice 3\nChoice 4",
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 3)

        question = Question.objects.last()
        self.assertEqual(question.question_text, "Updated MC question")
        self.assertEqual(question.question_type, Question.MULTICHOICES_QUESTION)
        self.assertSequenceEqual(question.possible_choices, ["Choice 1", "Choice 2", "Choice 3", "Choice 4"])

        question = self.create_question(question_text="Test DT question", question_type=Question.DATE_QUESTION,
                                        poll=poll)

        response = self.client.post(
            reverse("polls:update_question", args=(poll.id, question.id,)),
            {
                "question_text": "Updated DT question",
                "question_type": Question.DATE_QUESTION,
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 4)

        question = Question.objects.last()
        self.assertEqual(question.question_text, "Updated DT question")
        self.assertEqual(question.question_type, Question.DATE_QUESTION)

        question = self.create_question(question_text="Test OT question", question_type=Question.OPENTEXT_QUESTION,
                                        poll=poll)

        response = self.client.post(
            reverse("polls:update_question", args=(poll.id, question.id,)),
            {
                "question_text": "Updated OT question",
                "question_type": Question.OPENTEXT_QUESTION,
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 5)

        question = Question.objects.last()
        self.assertEqual(question.question_text, "Updated OT question")
        self.assertEqual(question.question_type, Question.OPENTEXT_QUESTION)

    def test_change_question_type_view(self):
        "Test that a question's type can be changed."
        poll = self.create_poll("Test poll", "Test description")

        question = self.create_question(question_text="Test MC question", question_type=Question.SINGLECHOICE_QUESTION,
                                        poll=poll, possible_choices=["Choice 1", "Choice 2"])

        response = self.client.post(
            reverse("polls:update_question", args=(poll.id, question.id,)),
            {
                "question_text": "Updated MC2DT question",
                "question_type": Question.DATE_QUESTION,
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 1)

        question = Question.objects.last()
        self.assertEqual(question.question_text, "Updated MC2DT question")
        self.assertEqual(question.question_type, Question.DATE_QUESTION)

        question = self.create_question(question_text="Test YN question", question_type=Question.YESNO_QUESTION,
                                        poll=poll)

        response = self.client.post(
            reverse("polls:update_question", args=(poll.id, question.id,)),
            {
                "question_text": "Updated YN2MC question",
                "question_type": Question.SINGLECHOICE_QUESTION,
                "possible_choices": "Choice 4\nChoice 5\nChoice 6",
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 2)

        question = Question.objects.last()
        self.assertEqual(question.question_text, "Updated YN2MC question")
        self.assertEqual(question.question_type, Question.SINGLECHOICE_QUESTION)
        self.assertSequenceEqual(question.possible_choices, ["Choice 4", "Choice 5", "Choice 6"])


class TestDeleteQuestionView(PollTestMixin):
    def test_delete_question_view(self):
        "Test that a question can be deleted."
        poll = self.create_poll("Test poll", "Test description")

        question1 = self.create_question(question_text="Test question 1", question_type=Question.YESNO_QUESTION, poll=poll)
        question2 = self.create_question(question_text="Test question 2", question_type=Question.DATE_QUESTION, poll=poll)

        response = self.client.post(reverse("polls:delete_question", args=(question2.id,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(Question.objects.last(), question1)
