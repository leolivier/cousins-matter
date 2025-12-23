import datetime
import random
import string
from django.urls import reverse
from django.utils import timezone, formats

from members.tests.tests_member_base import MemberTestCase
from ..models import EventPlanner, Question, Poll, PollAnswer, Answer

random.seed()


class PollTestBase(MemberTestCase):
  def set_dates(self, pub_days=0, duration=1):
    self.pub_date = timezone.now() + datetime.timedelta(days=pub_days)
    self.close_date = self.pub_date + datetime.timedelta(days=duration)

  def create_question(self, poll, question_text, question_type, possible_choices=None):
    """
    Create a question with the given `question_text` and `question_type`.
    The question is added to the given `poll`. For multiple choice questions,
    `choices` is a list of choices.
    """
    question = Question(
      question_text=question_text,
      question_type=question_type,
      poll=poll,
      possible_choices=possible_choices or [],
    )
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

  def random_choice(self, possible_choices, nb):
    max = len(possible_choices)
    rnd_idx = random.randint(0, max - 1)
    return [possible_choices[(rnd_idx + i) % max] for i in range(nb)]


class PollTestMixin(PollTestBase):
  def tearDown(self):
    super().tearDown()
    Poll.objects.all().delete()
    self.assertEqual(Question.objects.count(), 0)  # check delete cascade
    self.assertEqual(PollAnswer.objects.count(), 0)
    self.assertEqual(len(Answer.all_answers()), 0)

  def create_poll(self, title, description, open_to=Poll.OPEN_TO_ACTIVE, pub_days=-1, duration=2):
    """
    Create a poll with the given `title` and `description` and published the
    given number of `days` offset to now (negative for polls published
    in the past, positive for polls that have yet to be published) and closed in
    `duration` days after the publication date.
    """
    self.set_dates(pub_days, duration)
    poll = Poll(
      title=title,
      description=description,
      pub_date=self.pub_date,
      close_date=self.close_date,
      open_to=open_to,
      owner=self.member,
    )
    poll.save()
    self.assertEqual(Poll.objects.get(pk=poll.id), poll)
    return poll

  def create_questions(self, poll):
    rnd_str = "".join(random.choice(string.ascii_letters) for _ in range(10))
    possible_single_choices = ["Choice #1", "Choice #2", "Choice #3"]
    possible_multiple_choices = [
      "Choice #10",
      "Choice #20",
      "Choice #30",
      "Choice #40",
      "Choice #50",
    ]

    return [
      self.create_question(
        question_text=f"Test question 1 {rnd_str}",
        question_type=Question.YESNO_QUESTION,
        poll=poll,
      ),
      self.create_question(
        question_text=f"Test question 2 {rnd_str}",
        question_type=Question.DATE_QUESTION,
        poll=poll,
      ),
      self.create_question(
        question_text=f"Test question 3 {rnd_str}",
        question_type=Question.SINGLECHOICE_QUESTION,
        poll=poll,
        possible_choices=possible_single_choices,
      ),
      self.create_question(
        question_text=f"Test question 4 {rnd_str}",
        question_type=Question.OPENTEXT_QUESTION,
        poll=poll,
      ),
      self.create_question(
        question_text=f"Test question 5 {rnd_str}",
        question_type=Question.MULTICHOICES_QUESTION,
        poll=poll,
        possible_choices=possible_multiple_choices,
      ),
    ]

  def create_qnas(self, questions):
    rnd_str = "".join(random.choice(string.ascii_letters) for _ in range(10))
    rnd_date = timezone.localtime(
      timezone.make_aware(
        datetime.datetime(
          random.randint(2020, 2025),
          random.randint(1, 12),
          random.randint(1, 28),
          random.randint(0, 23),
          random.randint(0, 59),
        )
      )
    )
    rnd_bool = random.randint(0, 1) == 1
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
      {
        "question": questions[4],
        "answer": self.random_choice(questions[4].possible_choices, 2),
      },
    ]

  def create_and_check_answers(self, poll, expected_poll_answers=1):
    questions = poll.questions.all()
    qnas = self.create_qnas(questions)
    response = self.client.post(
      reverse("polls:vote", args=(poll.id,)),
      {f"q{qna['question'].id}-answer": qna["answer"] for qna in qnas},
      follow=True,
    )
    self.assertEqual(response.status_code, 200)
    self.assertEqual(PollAnswer.objects.count(), expected_poll_answers)
    poll_answer = PollAnswer.objects.filter(poll=poll, member=self.current_user()).first()

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


class EventPlannerTestMixin(PollTestBase):
  def tearDown(self):
    super().tearDown()
    EventPlanner.objects.all().delete()
    self.assertEqual(Question.objects.count(), 0)  # check delete cascade

  def get_possible_dates(self):
    now = timezone.now()
    dates = [now + datetime.timedelta(days=i + 1, hours=i + 1) for i in range(6)]
    return [datetime.datetime.strftime(date, "%Y-%m-%d %H:%M") for date in dates]

  def create_event_planner(
    self,
    title,
    description,
    open_to=Poll.OPEN_TO_ACTIVE,
    multiple_choices=False,
    pub_days=-1,
    duration=2,
  ):
    """
    Create an event planner with the given `title` and `description` and published the
    given number of `days` offset to now (negative for polls published
    in the past, positive for polls that have yet to be published) and closed in
    `duration` days after the publication date.
    """
    self.set_dates(pub_days, duration)
    event_planner = EventPlanner(
      title=title,
      description=description,
      pub_date=self.pub_date,
      close_date=self.close_date,
      open_to=open_to,
      owner=self.member,
      location="Somewhere over the rainbow",
    )
    event_planner.save()
    self.assertEqual(EventPlanner.objects.get(pk=event_planner.id), event_planner)
    question = self.create_question(
      question_text="Pick a date",
      question_type=Question.MULTIEVENTPLANNING_QUESTION if multiple_choices else Question.SINGLEEVENTPLANNING_QUESTION,
      poll=event_planner,
      possible_choices=self.get_possible_dates(),
    )
    self.assertEqual(Question.objects.count(), 1)
    self.assertEqual(Question.objects.first(), question)
    self.assertEqual(question.poll, event_planner)
    self.assertEqual(question.question_text, "Pick a date")
    return event_planner, question

  def check_display_info(self, event_planner, response):
    super().check_display_info(event_planner, response)
    if event_planner.location:
      self.assertContains(response, event_planner.location)
    if event_planner.chosen_date:
      time = timezone.localtime(event_planner.chosen_date)
      self.assertContains(response, formats.date_format(time, "SHORT_DATETIME_FORMAT"))

  def create_and_check_answers(self, event_planner, question, expected_poll_answers=1):
    questions = event_planner.questions.all()
    self.assertNotEqual(len(questions), 0)
    date_question = questions[0]
    self.assertEqual(date_question, question)
    self.assertIn(date_question.question_type, Question.EVENT_TYPES)
    nb_dates = 1 if date_question.question_type == Question.SINGLEEVENTPLANNING_QUESTION else 2
    dates = self.random_choice(date_question.possible_choices, nb_dates)
    response = self.client.post(
      reverse("polls:event_planner_vote", args=(event_planner.id,)),
      {f"q{date_question.id}-answer": "\n".join(dates)},
      follow=True,
    )
    self.assertEqual(response.status_code, 200)
    self.assertEqual(PollAnswer.objects.count(), expected_poll_answers)
    poll_answer = PollAnswer.objects.filter(poll=event_planner, member=self.current_user()).first()

    answers = Answer.filter_answers(poll_answer=poll_answer)
    self.assertEqual(len(answers), 1)

    answer = answers[0]
    self.assertEqual(answer.question, date_question)
    self.assertEqual(
      answer.answer,
      dates[0] if date_question.question_type == Question.SINGLEEVENTPLANNING_QUESTION else dates,
    )
