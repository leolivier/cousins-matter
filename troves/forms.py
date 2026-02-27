from django import forms
from .models import Trove
from core.widgets import RichTextarea


class TreasureForm(forms.ModelForm):
  class Meta:
    model = Trove
    fields = ["title", "description", "picture", "file", "category"]
    widgets = {
      "description": RichTextarea(),
    }
