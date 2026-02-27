from django.forms.widgets import Textarea


# widgets using this class will have the richtextarea css class
# see core/templates/core/common/include-summernote.html for usage
class RichTextarea(Textarea):
  pass
