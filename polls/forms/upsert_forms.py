import datetime
from django import forms
from django.utils.translation import gettext_lazy as _

from cm_main.utils import allowed_date_formats, parse_locale_date, translate_date_format
from ..models import EventPlanner, Poll, Question


# forms for creating/updating Polls, Questions, and Answers definitions
class PollUpsertForm(forms.ModelForm):
  class Meta:
    model = Poll
    fields = [
      "title",
      "description",
      "pub_date",
      "close_date",
      "open_to",
      "closed_list",
    ]
    labels = {
      "title": _("Title"),
      "pub_date": _("To be published on"),
      "close_date": _("To be closed on"),
      "open_to_all": _("Open to all"),
      "open_to_active": _("Open to active members"),
      "closed_list": _("Closed list"),
    }


class EventPlannerUpsertForm(forms.ModelForm):
  multichoices_planner = forms.BooleanField(label=_("Allow choosing multiple dates in the answer"), required=False)
  possible_dates = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=True)

  class Meta:
    model = EventPlanner
    fields = [
      "title",
      "description",
      "location",
      "possible_dates",
      "multichoices_planner",
      "chosen_date",
      "pub_date",
      "close_date",
      "open_to",
      "closed_list",
    ]
    labels = {
      "title": _("Title"),
      "pub_date": _("To be published on"),
      "close_date": _("To be closed on"),
      "location": _("Location"),
      "chosen_date": _("Chosen date"),
      "open_to_all": _("Open to all"),
      "open_to_active": _("Open to active members"),
      "closed_list": _("Closed list"),
    }

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields["possible_dates"].help_text = _(
      "Provide the possible dates and times, one per line. Allowed formats are: "
    ) + ", ".join([translate_date_format(date_format) for date_format in allowed_date_formats()])

    if "instance" in kwargs:
      date_question = Question.objects.filter(poll=kwargs["instance"], question_type__in=Question.EVENT_TYPES).first()
      self.fields["possible_dates"].initial = "\n".join(date_question.possible_choices)
      self.fields["multichoices_planner"].initial = date_question.question_type == Question.MULTIEVENTPLANNING_QUESTION

  def clean_possible_dates(self):
    data = self.cleaned_data["possible_dates"]
    possible_dates = [date.strip() for date in data.split("\n") if date.strip()]
    possible_dates = list(set(possible_dates))  # remove duplicates
    if len(possible_dates) < 2:
      raise forms.ValidationError(_("You must provide at least two possible dates!"))
    for date in possible_dates:
      # will raise an exception if the date is not valid
      real_date = parse_locale_date(date)
      if datetime.datetime.now() > real_date:
        raise forms.ValidationError(date + ": " + _("All dates must be in the future!"))
    return possible_dates


class QuestionUpsertForm(forms.ModelForm):
  possible_choices = forms.CharField(
    widget=forms.Textarea(attrs={"rows": 5, "cols": 60}),
    help_text=_("Provide the possible choices, one per line"),
    required=False,
  )

  class Meta:
    model = Question
    fields = ["question_text", "question_type", "possible_choices"]

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if "instance" in kwargs and kwargs["instance"] and kwargs["instance"].question_type in Question.CHOICE_TYPES:
      self.initial["possible_choices"] = "\n".join(kwargs["instance"].possible_choices)
    else:
      self.initial["possible_choices"] = ""
    # print("initial choices:", self.initial["possible_choices"])

  def clean_possible_choices(self):
    if self.cleaned_data["question_type"] not in Question.CHOICE_TYPES:
      return []
    data = self.cleaned_data["possible_choices"]
    print("choices:", data)
    possible_choices = [choice.strip() for choice in data.split("\n") if choice.strip()]
    if len(possible_choices) < 2:
      raise forms.ValidationError(_("You must provide at least two possible choices!"))
    return possible_choices
