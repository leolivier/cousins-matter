import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _, gettext
from django.utils import timezone, formats
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

    class Meta:
        verbose_name = _('poll')
        verbose_name_plural = _('polls')
        ordering = ['pub_date']

    def __str__(self):
        return self.title

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

    def get_results(self, user=None):
        """
        This method returns the results of the poll as an array of dictionaries, one for each question.
        Each dictionary has the following keys:
        - question: the question
        - user_answer: answer provided by the user (if any)
        - total_answers: total number of answers for this question
        - result: can be:
            - the percentage of positive answers for this question for yes/no questions
            - the percentage of each choice for multiple choice questions as a dictionary {choice: percentage}
            - the different answers for open text questions as an array of strings
            - the different dates for date questions as an array of strings
        """
        results = []
        for question in self.questions.all():
            question_result = QuestionResult(question)
            question_result.build_result(user)
            results.append(question_result)
        return results


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

    class Meta:
        verbose_name = _('question')
        verbose_name_plural = _('questions')
        ordering = ['id']

    def __str__(self):
        return self.question_text


class PollAnswer(models.Model):
    'Answers provided by members to Poll questions.'
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('poll answer')
        verbose_name_plural = _('poll answers')


class Answer(models.Model):
    'Abstract answer provided by a member to a question. Must be subclassed.'
    poll_answer = models.ForeignKey(PollAnswer, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name='answers_%(class)s', on_delete=models.CASCADE)
    question_type = None
    answer = None

    class Meta:
        abstract = True
        verbose_name = _('answer')
        verbose_name_plural = _('answers')

    @staticmethod
    def filter_answers(**kwargs):
        results = []
        for subclass in Answer.__subclasses__():
            results.extend(list(subclass.objects.filter(**kwargs)))
        return results

    @staticmethod
    def all_answers():
        results = []
        for subclass in Answer.__subclasses__():
            results.extend(list(subclass.objects.all()))
        return results

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

    class Meta:
        verbose_name = _('choice answer')
        verbose_name_plural = _('choice answers')

    def __str__(self):
      "Return the text of the selected choice as a string representation of the ChoiceAnswer."
      return self.answer

    @staticmethod
    def compute_result(answers, result):
        'Compute the result for a list of ChoiceAnswers.'
        choice_results = {}
        for choice in result.question.possible_choices:
            choice_answers = answers.filter(answer=choice).count()
            choice_results[choice] = (choice_answers / result.total_answers) * 100 if result.total_answers > 0 else 0
        return [f"{key}: {value}%" for key, value in choice_results.items()] if choice_results else ["-"]


class YesNoAnswer(Answer):
    question_type = Question.YESNO_QUESTION
    'Answer provided by a member to a yes/no question.'
    answer = models.BooleanField(_('answer'), default=False)

    class Meta:
        verbose_name = _('yes/no answer')
        verbose_name_plural = _('yes/no answers')

    def __str__(self):
        return gettext("Yes") if self.answer else gettext("No")

    @staticmethod
    def compute_result(answers, result):
        'Compute the result for a list of YesNoAnswers as a percentage of positive answers.'
        return [f"{(answers.filter(answer=True).count() / result.total_answers) * 100 if result.total_answers > 0 else 0}%"]


class TextAnswer(Answer):
    question_type = Question.OPENTEXT_QUESTION
    'Answer provided by a member to an open text question.'
    answer = models.TextField(_('answer'), default="", blank=True, max_length=500)

    class Meta:
        verbose_name = _('text answer')
        verbose_name_plural = _('text answers')

    def __str__(self):
        return self.answer

    @staticmethod
    def compute_result(answers, result):
        'Compute the result for a list of TextAnswers.'
        return ["-"] if result.total_answers == 0 else list(answers.values_list('answer', flat=True))


class DateTimeAnswer(Answer):
    question_type = Question.DATE_QUESTION
    'Answer provided by a member to an date/time question.'
    answer = models.DateTimeField(_('answer'), default=timezone.now)

    class Meta:
        verbose_name = _('date answer')
        verbose_name_plural = _('date answers')

    def __str__(self):
        return formats.date_format(self.answer, "DATETIME_FORMAT")

    @staticmethod
    def compute_result(answers, result):
        'Compute the result for a list of DateTimeAnswers.'
        return ["-"] if result.total_answers == 0 else list(answers.values_list('answer', flat=True))


class QuestionResult:
    question: Question
    result: list = []
    total_answers: int = 0
    user_answer: str = "-"

    def __init__(self, question):
        self.question = question

    def build_result(self, user=None):
        answer_class = Answer.get_answer_class_for_question_type(self.question.question_type)
        answers = answer_class.objects.filter(question=self.question)
        self.total_answers = answers.count()
        self.result = answer_class.compute_result(answers, self)
        if user:
            user_answer = answers.filter(poll_answer__member=user).first()
            if user_answer:
                self.user_answer = str(user_answer)
