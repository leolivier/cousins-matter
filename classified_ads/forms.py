from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from .models import AdPhoto, ClassifiedAd, Categories

from crispy_forms.helper import FormHelper
from crispy_bulma.layout import Layout, Row, Column
from cm_main.widgets import RichTextarea


class ClassifiedAdForm(forms.ModelForm):
  category = forms.ChoiceField(
    choices=[("", _("Select a category")), *Categories.list_categories()],
    widget=forms.Select(
      attrs={
        "hx-get": reverse_lazy("classified_ads:get_subcategories"),
        "hx-target": "#id_subcategory",
      }
    ),
    required=True,
  )
  subcategory = forms.ChoiceField(
    choices=[("", _("Select a subcategory"))],  # Will be populated in get_subcategories view
    widget=forms.Select(),
    required=False,
  )

  class Meta:
    model = ClassifiedAd
    exclude = ["owner"]
    widgets = {
      "description": RichTextarea(),
    }

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    try:
      if self.instance and self.instance.category:
        self.fields["subcategory"].choices = Categories.list_subcategories(self.instance.category)
    except Exception as e:
      print(f"Error retrieving categories and subcategories : {e}")

    # crispy bulma does not implement layouts I need :/
    self.helper = FormHelper(self)
    self.helper.form_tag = False
    all_fields = list(self.fields.keys())
    # fields with a special layout
    special_fields = ["title", "category", "subcategory"]
    other_fields = [field for field in all_fields if field not in special_fields]

    # Define the custom layout: first the line with the two fields side by side,
    # then let crispy automatically display the other fields.
    self.helper.layout = Layout(
      "title",
      Row(
        Column("category", css_class="is-6"),
        Column("subcategory", css_class="is-6"),
      ),
      # Then automatically add the other fields in the natural order:
      *other_fields,
    )
    # print(self.helper.layout.__dict__)

  def is_valid(self):
    # set the subcategory choices before checking validity
    if "category" in self.data:
      if self.data["category"] not in Categories.list_category_keys():
        return False
      self.fields["subcategory"].choices = Categories.list_subcategories(self.data["category"])
    return super().is_valid()


class AdPhotoForm(forms.ModelForm):
  class Meta:
    model = AdPhoto
    fields = ["image"]


class MessageForm(forms.Form):
  message = forms.CharField(widget=forms.Textarea(attrs={"rows": 4, "cols": 50}))

  class Meta:
    widgets = {
      "message": RichTextarea(),
    }
