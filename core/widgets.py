from django.forms.widgets import DateInput, Textarea


# widgets using this class will have the richtextarea css class
# see core/templates/core/common/include-summernote.html for usage
class RichTextarea(Textarea):
  pass


class BulmaCalendar(DateInput):
  def __init__(self, attrs=None, format=None):
    if attrs is None:
      attrs = {"type": "date"}
    else:
      attrs["type"] = "date"
    if format is None:
      format = "%Y-%m-%d"
    super().__init__(attrs, format)
