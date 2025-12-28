from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Person, Family


class DateInput(forms.DateInput):
  input_type = "date"

  def __init__(self, attrs=None, format=None):
    if not format:
      format = "%Y-%m-%d"
    super().__init__(attrs, format)


class PersonForm(forms.ModelForm):
  class Meta:
    model = Person
    fields = [
      "first_name",
      "last_name",
      "sex",
      "birth_date",
      "birth_place",
      "death_date",
      "death_place",
      "notes",
      "member",
      "child_of_family",
    ]
    widgets = {
      "birth_date": DateInput(),
      "death_date": DateInput(),
      "notes": forms.Textarea(attrs={"rows": 3}),
    }


class FamilyForm(forms.ModelForm):
  class Meta:
    model = Family
    fields = [
      "partner1",
      "partner2",
      "union_type",
      "union_date",
      "union_place",
      "separation_date",
    ]
    widgets = {
      "union_date": DateInput(),
      "separation_date": DateInput(),
    }


class GedcomImportForm(forms.Form):
  gedcom_file = forms.FileField(
    label=_("GEDCOM File"),
    help_text=_("Upload a .ged file to import your genealogy data."),
  )
