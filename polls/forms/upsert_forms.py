from django import forms
from django.utils.translation import gettext_lazy as _
from ..models import Poll, Question


# forms for creating/updating Polls, Questions, and Answers definitions
class PollUpsertForm(forms.ModelForm):
  class Meta:
    model = Poll
    fields = ['title', 'description', 'pub_date', 'close_date', 'open_to', 'closed_list']
    labels = {'title': _('Title'), 'pub_date': _('To be published on'), 'close_date': _('To be closed on'),
              'open_to_all': _('Open to all'), 'open_to_active': _('Open to active members'),
              'closed_list': _('Closed list')}


class QuestionUpsertForm(forms.ModelForm):
  possible_choices = forms.CharField(
    widget=forms.Textarea(attrs={'rows': 5, 'cols': 60}),
    help_text=_("Provide the possible choices, one per line"),
    required=False
  )

  class Meta:
    model = Question
    fields = ['question_text', 'question_type', 'possible_choices']

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if 'instance' in kwargs and kwargs['instance'].question_type == Question.MULTICHOICES_QUESTION:
        self.fields['possible_choices'].initial = '\n'.join(kwargs['instance'].possible_choices)

  def clean_possible_choices(self):
    data = self.cleaned_data['possible_choices']
    possible_choices = [choice.strip() for choice in data.split("\n") if choice.strip()]
    return possible_choices
