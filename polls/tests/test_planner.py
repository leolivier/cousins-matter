import datetime
from django.urls import reverse
from django.utils import timezone
from .test_base import EventPlannerTestMixin
from ..models import EventPlanner, Poll, Question


class EventPlannerUpsertTest(EventPlannerTestMixin):
    def test_create_event_planner_view(self):
        response = self.client.get(reverse("polls:create_event_planner"))
        self.assertEqual(response.status_code, 200)
        self.set_dates(pub_days=-1, duration=2)
        possible_dates = self.get_possible_dates()
        response = self.client.post(
            reverse("polls:create_event_planner"),
            {
                "title": "Test event planner",
                "description": "Event planner description",
                "pub_date": self.pub_date.isoformat(),
                "close_date": self.close_date.isoformat(),
                "open_to": Poll.OPEN_TO_ACTIVE,
                "possible_dates": "\n".join(possible_dates),
                "multichoices_planner": False
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        # self.print_response(response)
        self.assertEqual(EventPlanner.objects.count(), 1)
        self.assertEqual(Poll.objects.count(), 1)

        event_planner = EventPlanner.objects.first()
        self.assertEqual(event_planner.title, "Test event planner")
        self.assertEqual(event_planner.description, "Event planner description")
        self.assertEqual(event_planner.pub_date, self.pub_date)
        self.assertEqual(event_planner.close_date, self.close_date)
        self.assertEqual(event_planner.open_to, Poll.OPEN_TO_ACTIVE)
        self.assertEqual(Poll.objects.first().eventplanner, event_planner)

        date_question = Question.objects.filter(poll=event_planner).first()
        self.assertIsNotNone(date_question)
        self.assertEqual(date_question.question_type, Question.SINGLEEVENTPLANNING_QUESTION)
        self.assertSetEqual(set(date_question.possible_choices), set(possible_dates))

    def test_update_event_planner_view(self):
        event_planner, question = self.create_event_planner("Test event planner", "Event planner description")
        # add a yes no question
        self.create_question(question_text="Test question 1", question_type=Question.YESNO_QUESTION, poll=event_planner)
        response = self.client.get(reverse("polls:update_event_planner", args=(event_planner.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test question 1")
        # the planner base question is not shown in the questions list
        self.assertNotContains(response, question.question_text)

        pub_date = self.pub_date + datetime.timedelta(days=1)
        close_date = self.close_date + datetime.timedelta(days=1)
        possible_dates = self.get_possible_dates()

        response = self.client.post(
            reverse("polls:update_event_planner", args=(event_planner.id,)),
            {
                "title": "Updated event planner",
                "description": "Updated event planner description",
                "pub_date": pub_date.isoformat(),
                "close_date": close_date.isoformat(),
                "open_to": Poll.OPEN_TO_ALL,
                "possible_dates": "\n".join(possible_dates),
                "multichoices_planner": True,
                "chosen_date": possible_dates[2]
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(EventPlanner.objects.count(), 1)
        self.assertEqual(Poll.objects.count(), 1)

        event_planner = EventPlanner.objects.first()
        self.assertEqual(event_planner.title, "Updated event planner")
        self.assertEqual(event_planner.description, "Updated event planner description")
        self.assertEqual(event_planner.pub_date, pub_date)
        self.assertEqual(event_planner.close_date, close_date)
        self.assertEqual(event_planner.open_to, Poll.OPEN_TO_ALL)
        chosen_date = timezone.localtime(event_planner.chosen_date)
        self.assertEqual(datetime.datetime.strftime(chosen_date, "%Y-%m-%d %H:%M"), possible_dates[2])
        self.assertEqual(Poll.objects.first().eventplanner, event_planner)

        date_question = Question.objects.filter(poll=event_planner).first()
        self.assertEqual(date_question, question)
        self.assertEqual(date_question.question_type, Question.MULTIEVENTPLANNING_QUESTION)
        self.assertSetEqual(set(date_question.possible_choices), set(possible_dates))


class EventPlannerDeleteViewTest(EventPlannerTestMixin):
    def test_delete_event_planner_view(self):
        event_planner, question = self.create_event_planner("Test event planner", "Event planner description")
        response = self.client.post(reverse("polls:delete_event_planner", args=(event_planner.id,)), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(EventPlanner.objects.count(), 0)
        self.assertEqual(Question.objects.count(), 0)


class EventPlannerVoteViewTest(EventPlannerTestMixin):
    def test_event_planner_vote_view(self):
        event_planner, question = self.create_event_planner("Test event planner", "Event planner description")
        self.create_and_check_answers(event_planner, question, expected_poll_answers=1)
