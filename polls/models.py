import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from members.models import Member


class Poll(models.Model):
    OPEN_TO_ALL = 'all'
    OPEN_TO_ACTIVE = 'act'
    OPEN_TO_CLOSED = 'lst'
    OPEN_TO_TYPES = (
        (OPEN_TO_ALL, _('All members')),
        (OPEN_TO_ACTIVE, _('Active members only')),
        (OPEN_TO_CLOSED, _('Closed list')),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(default="", blank=True, max_length=500)
    owner = models.ForeignKey(Member, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    pub_date = models.DateTimeField(null=True, blank=True, default=timezone.now)
    close_date = models.DateTimeField(null=True, blank=True)
    open_to = models.CharField(max_length=3, choices=OPEN_TO_TYPES, default=OPEN_TO_ACTIVE)
    closed_list = models.ManyToManyField(Member, related_name='closed_list', blank=True)

    def __str__(self):
        return self.title

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Question(models.Model):
    '''
    Question model for Polls.
    Question types are Yes/No, Multiple Choice, and Open Text.
    A question can have multiple choices. In that case, it has a list of predefined Choices
    linked to it which are the possible answers.
    '''
    YESNO_QUESTION = 'YN'
    MULTICHOICES_QUESTION = 'MC'
    OPENTEXT_QUESTION = 'OT'
    DATE_QUESTION = 'DT'
    QUESTION_TYPES = (
        (YESNO_QUESTION, _('Yes/No')),
        (MULTICHOICES_QUESTION, _('Multiple Choice')),
        (OPENTEXT_QUESTION, _('Open Text')),
        (DATE_QUESTION, _('Date')),
    )
    poll = models.ForeignKey(Poll, related_name='questions', on_delete=models.CASCADE)
    question_text = models.CharField(_('Question'), max_length=200)
    question_type = models.CharField(_('Question Type'), max_length=2, choices=QUESTION_TYPES, default=YESNO_QUESTION)
    # one JSON array string that contains the possible choices when question_type is MC
    possible_choices = models.JSONField(_('Possible choices'), default=list, blank=True)

    def __str__(self):
        return self.question_text


class PollAnswer(models.Model):
    'Answers provided by members to Poll questions.'
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)


class Answer(models.Model):
    'Abstract answer provided by a member to a question. Must be subclassed.'
    poll_answer = models.ForeignKey(PollAnswer, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name='answers_%(class)s', on_delete=models.CASCADE)
    question_type = None
    answer = None

    class Meta:
        abstract = True

    @staticmethod
    def filter_answers(**kwargs):
        results = []
        for subclass in Answer.__subclasses__():
            results.append(list(subclass.objects.filter(**kwargs)))

    @property
    def text(self):
        return str(self)

    @staticmethod
    def get_answer_class_for_question_type(question_type):
        'Returns the Answer class corresponding to the question type.'
        for subclass in Answer.__subclasses__():
            if subclass.question_type == question_type:
                return subclass
        raise ValueError(f"No Answer subclass found for question type {question_type}")


class ChoiceAnswer(Answer):
    question_type = Question.MULTICHOICES_QUESTION
    'Answer provided by a member to a multiple choice question.'
    answer = models.CharField(_('choice'), max_length=100, default="", blank=True)

    def __str__(self):
      "Return the text of the selected choice as a string representation of the ChoiceAnswer."
      return self.answer


class YesNoAnswer(Answer):
    question_type = Question.YESNO_QUESTION
    'Answer provided by a member to a yes/no question.'
    answer = models.BooleanField(_('answer'), default=False)

    def __str__(self):
        return str(self.answer)


class TextAnswer(Answer):
    question_type = Question.OPENTEXT_QUESTION
    'Answer provided by a member to an open text question.'
    answer = models.TextField(_('answer'), default="", blank=True, max_length=500)

    def __str__(self):
        return self.answer


class DateTimeAnswer(Answer):
    question_type = Question.DATE_QUESTION
    'Answer provided by a member to an date/time question.'
    answer = models.DateTimeField(_('answer'), default=timezone.now)

    def __str__(self):
        return str(self.answer)
