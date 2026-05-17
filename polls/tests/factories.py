import factory
from factory.django import DjangoModelFactory
from polls.models import Poll, Question, PollAnswer, YesNoAnswer
from members.tests.factories import MemberFactory


class PollFactory(DjangoModelFactory):
  class Meta:
    model = Poll

  title = factory.Faker("sentence")
  description = factory.Faker("paragraph")
  owner = factory.SubFactory(MemberFactory)


class QuestionFactory(DjangoModelFactory):
  class Meta:
    model = Question

  poll = factory.SubFactory(PollFactory)
  question_text = factory.Faker("sentence", nb_words=6)
  question_type = Question.YESNO_QUESTION


class PollAnswerFactory(DjangoModelFactory):
  class Meta:
    model = PollAnswer

  poll = factory.SubFactory(PollFactory)
  member = factory.SubFactory(MemberFactory)


class YesNoAnswerFactory(DjangoModelFactory):
  class Meta:
    model = YesNoAnswer

  poll_answer = factory.SubFactory(PollAnswerFactory)
  question = factory.SubFactory(QuestionFactory)
  answer = factory.Faker("boolean")
