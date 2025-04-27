from django import forms
from django.utils.translation import gettext_lazy as _

from cm_main.widgets import RichTextarea

from ..models import (
  MultiChoiceAnswer,
  MultiEventAnswer,
  Question,
  SingleEventAnswer,
  YesNoAnswer,
  ChoiceAnswer,
  TextAnswer,
  DateTimeAnswer,
  Answer
)


class AnswerFormMixin:
  models_dict = {}

  def __init_subclass__(cls):
    super().__init_subclass__()
    AnswerFormMixin.models_dict[cls.Meta.model] = cls

  def __init__(self, *args, **kwargs):
    instance = kwargs.get('instance')
    if kwargs.get('question'):
      self.question = kwargs.pop('question')  # Remove the question from kwargs
    elif instance:
      self.question = instance.question
    super().__init__(*args, **kwargs)
    self.fields['answer'].label = self.question.question_text
    # print(self.fields['answer'].__dict__)


def get_answerform_class_for_question_type(question_type):
    'Returns the AnswerForm subclass corresponding to the question type.'
    try:
      answerClass = Answer.get_answer_class_for_question_type(question_type)
      return AnswerFormMixin.models_dict[answerClass]
    except KeyError:
      raise ValueError(f"No AnswerForm subclass found for question type {question_type}")


# forms for answering Polls
class YesNoAnswerForm(AnswerFormMixin, forms.ModelForm):
  class Meta:
    model = YesNoAnswer
    fields = ['answer']
    help_texts = {'answer': _('Check the box if Yes')}


class ChoiceAnswerForm(AnswerFormMixin, forms.ModelForm):
  answer = forms.ChoiceField(required=True, label=_('choice'), help_text=_('Select one choice'))

  class Meta:
    model = ChoiceAnswer
    fields = ['answer']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if self.question.question_type not in Question.SINGLECHOICE_TYPES:
      raise ValueError('question must be for a Single Choice question')
    self.fields['answer'].choices = [(choice, choice) for choice in self.question.possible_choices]


class EventAnswerForm(ChoiceAnswerForm):
  class Meta:
    model = SingleEventAnswer
    fields = ['answer']


class TextAnswerForm(AnswerFormMixin, forms.ModelForm):
  class Meta:
    model = TextAnswer
    fields = ['answer']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['answer'].widget = RichTextarea()


class DateAnswerForm(AnswerFormMixin, forms.ModelForm):
  class Meta:
    model = DateTimeAnswer
    fields = ['answer']


class MultipleChoiceAnswerForm(AnswerFormMixin, forms.ModelForm):
  answer = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_('choice'),
        help_text=_('Select your choices'))

  class Meta:
    model = MultiChoiceAnswer
    fields = ['answer']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if self.question.question_type not in Question.MULTICHOICES_TYPES:
      raise ValueError('question must be for a Multiple Choices question')
    self.fields['answer'].choices = [(choice, choice) for choice in self.question.possible_choices]


class MultiEventAnswerForm(MultipleChoiceAnswerForm):
  class Meta:
    model = MultiEventAnswer
    fields = ['answer']
