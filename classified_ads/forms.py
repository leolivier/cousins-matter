from django import forms
# from django.utils.translation import gettext as _
from .models import AdPhoto, ClassifiedAd, Categories
# from crispy_forms.helper import FormHelper
# from crispy_forms.layout import Layout, Fieldset
from cm_main.widgets import RichTextarea


class ClassifiedAdForm(forms.ModelForm):
  category = forms.ChoiceField(
    choices=[],  # Will be populated in __init__.
    widget=forms.Select(),
    required=True
  )
  subcategory = forms.ChoiceField(
    choices=[],  # Will be populated either in __init__ or in the javascript based on the selected category.
    widget=forms.Select(),
    required=False
  )

  class Meta:
    model = ClassifiedAd
    exclude = ['owner']
    widgets = {
      'description': RichTextarea(),
    }

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    try:
      categories_choices = Categories.list_categories()
      if self.instance and self.instance.category:
        subcategories_choices = Categories.list_subcategories(self.instance.category)
      else:
        subcategories_choices = []
    except Exception as e:
      print(f"Error retrieving categories and subcategories : {e}")
      categories_choices = []
      subcategories_choices = []

    self.fields['category'].choices = categories_choices
    self.fields['subcategory'].choices = subcategories_choices

    # crispy bulma does not implement layouts I need :/
    # # Initialize the crispy form helper
    # self.helper = FormHelper(self)
    # all_fields = list(self.fields.keys())
    # # fields with a special layout
    # special_fields = ['title', 'category', 'subcategory']
    # other_fields = [field for field in all_fields if field not in special_fields]

    # # Define the custom layout: first the line with the two fields side by side,
    # # then let crispy automatically display the other fields.
    # self.helper.layout = Layout(
    #   'title',
    #   Fieldset("Text for the label {{ username }}", 'category', 'subcategory'),
    #   # Then automatically add the other fields in the natural order:
    #   *other_fields
    # )
    # print(self.helper.layout)

  def is_valid(self):
    # set the subcategory choices before checking validity
    if 'category' in self.data:
      if self.data['category'] not in Categories.list_category_keys():
        return False
      self.fields['subcategory'].choices = Categories.list_subcategories(self.data['category'])
    return super().is_valid()


class AdPhotoForm(forms.ModelForm):

  class Meta:
    model = AdPhoto
    fields = ['image']


class MessageForm(forms.Form):
  message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 50}))

  class Meta:
    widgets = {
      'message': RichTextarea(),
    }
