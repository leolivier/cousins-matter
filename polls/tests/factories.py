import factory
import random
from factory.django import DjangoModelFactory
from polls.models import Poll, Question, PollAnswer, YesNoAnswer, TextAnswer, DateTimeAnswer, ChoiceAnswer, MultiChoiceAnswer
from members.tests.factories import MemberFactory


class PollFactory(DjangoModelFactory):
  class Meta:
    model = Poll

  title = factory.Faker("sentence")
  description = factory.Faker("paragraph")
  owner = factory.SubFactory(MemberFactory)

  @factory.post_generation
  def create_questions(self, create, extracted, **kwargs):
    if not create or extracted is False:
      return

    # 1. Yes/No Question
    QuestionFactory(
      poll=self, question_text="Est-ce que vous aimez cette fonctionnalité ?", question_type=Question.YESNO_QUESTION
    )

    # 2. Choice Question (Single Choice)
    QuestionFactory(
      poll=self,
      question_text="Quelle est votre couleur préférée ?",
      question_type=Question.SINGLECHOICE_QUESTION,
      possible_choices=["Rouge", "Vert", "Bleu", "Jaune"],
    )

    # 3. Multiple Choice Question
    QuestionFactory(
      poll=self,
      question_text="Quels jours êtes-vous disponible ?",
      question_type=Question.MULTICHOICES_QUESTION,
      possible_choices=["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
    )

    # 4. Open Text Question
    QuestionFactory(
      poll=self, question_text="Avez-vous des suggestions d'amélioration ?", question_type=Question.OPENTEXT_QUESTION
    )

    # 5. Date Question
    QuestionFactory(
      poll=self, question_text="Quand devrions-nous organiser la prochaine réunion ?", question_type=Question.DATE_QUESTION
    )


class QuestionFactory(DjangoModelFactory):
  class Meta:
    model = Question

  poll = factory.SubFactory(PollFactory)
  question_text = factory.Faker("sentence", nb_words=6)
  question_type = Question.YESNO_QUESTION
  possible_choices = []


class PollAnswerFactory(DjangoModelFactory):
  class Meta:
    model = PollAnswer

  poll = factory.SubFactory(PollFactory)
  member = factory.SubFactory(MemberFactory)

  @factory.post_generation
  def create_answers(self, create, extracted, **kwargs):
    if not create or extracted is False:
      return

    # Automatically create the corresponding Answer model for each question in the poll
    for question in self.poll.questions.all():
      if question.question_type == Question.YESNO_QUESTION:
        YesNoAnswerFactory(poll_answer=self, question=question)
      elif question.question_type == Question.SINGLECHOICE_QUESTION:
        ChoiceAnswerFactory(poll_answer=self, question=question)
      elif question.question_type == Question.MULTICHOICES_QUESTION:
        MultiChoiceAnswerFactory(poll_answer=self, question=question)
      elif question.question_type == Question.OPENTEXT_QUESTION:
        TextAnswerFactory(poll_answer=self, question=question)
      elif question.question_type == Question.DATE_QUESTION:
        DateTimeAnswerFactory(poll_answer=self, question=question)


class YesNoAnswerFactory(DjangoModelFactory):
  class Meta:
    model = YesNoAnswer

  poll_answer = factory.SubFactory(PollAnswerFactory)
  question = factory.SubFactory(QuestionFactory)
  answer = factory.Faker("boolean")


class TextAnswerFactory(DjangoModelFactory):
  class Meta:
    model = TextAnswer

  poll_answer = factory.SubFactory(PollAnswerFactory)
  question = factory.SubFactory(QuestionFactory)
  answer = factory.Faker("paragraph")


class DateTimeAnswerFactory(DjangoModelFactory):
  class Meta:
    model = DateTimeAnswer

  poll_answer = factory.SubFactory(PollAnswerFactory)
  question = factory.SubFactory(QuestionFactory)
  answer = factory.Faker("date_time_this_decade")


class ChoiceAnswerFactory(DjangoModelFactory):
  class Meta:
    model = ChoiceAnswer

  poll_answer = factory.SubFactory(PollAnswerFactory)
  question = factory.SubFactory(QuestionFactory)

  @factory.lazy_attribute
  def answer(self):
    choices = self.question.possible_choices
    return random.choice(choices) if choices else "Option A"


class MultiChoiceAnswerFactory(DjangoModelFactory):
  class Meta:
    model = MultiChoiceAnswer

  poll_answer = factory.SubFactory(PollAnswerFactory)
  question = factory.SubFactory(QuestionFactory)

  @factory.lazy_attribute
  def answer(self):
    choices = self.question.possible_choices
    if choices:
      k = random.randint(1, len(choices))
      return random.sample(choices, k)
    return ["Option A"]
