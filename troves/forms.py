from django import forms
from .models import Trove
from cm_main.widgets import RichTextarea


class TreasureForm(forms.ModelForm):
  class Meta:
    model = Trove
    fields = ['description', 'picture', 'file', 'category']
    widgets = {
      'description': RichTextarea(),
    }
