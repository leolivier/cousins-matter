from django import forms
from django.utils.translation import gettext_lazy as _

from ..models import YesNoAnswer, ChoiceAnswer, TextAnswer, DateTimeAnswer, Answer


class AnswerFormMixin:
  def __init__(self, *args, **kwargs):
    instance = kwargs.get('instance')
    if instance:
      self.question = instance.question
    elif kwargs.get('question'):
      self.question = kwargs.pop('question')  # Remove the question from kwargs
    super().__init__(*args, **kwargs)
    self.fields['answer'].label = self.question.question_text
    # print(self.fields['answer'].__dict__)


def get_answerform_class_for_question_type(question_type):
    'Returns the AnswerForm subclass corresponding to the question type.'
    answerClass = Answer.get_answer_class_for_question_type(question_type)
    for subclass in AnswerFormMixin.__subclasses__():
        if subclass.Meta.model == answerClass:
            return subclass
    raise ValueError(f"No AnswerForm subclass found for question type {question_type}")


# forms for answering Polls
class YesNoAnswerForm(AnswerFormMixin, forms.ModelForm):
  class Meta:
    model = YesNoAnswer
    fields = ['answer']
    help_texts = {'answer': _('Check the box if Yes')}


class ChoiceAnswerForm(AnswerFormMixin, forms.ModelForm):
  class Meta:
    model = ChoiceAnswer
    fields = ['answer']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if self.question.question_type != 'MC':
      raise ValueError('question must be for a Multiple Choice question')
    self.fields['answer'].choices = self.question.possible_choices


class TextAnswerForm(AnswerFormMixin, forms.ModelForm):
  class Meta:
    model = TextAnswer
    fields = ['answer']


class DateAnswerForm(AnswerFormMixin, forms.ModelForm):
  class Meta:
    model = DateTimeAnswer
    fields = ['answer']
