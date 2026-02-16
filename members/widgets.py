from typing import Any
from django.forms import Widget


class FieldLinkWrapper(Widget):
  template_name = "widgets/wrap_create_link.html"

  def __init__(
    self,
    widget,
    can_add_related,
    can_change_related,
    add_url=None,
    add_title=None,
    change_url=None,
    change_title=None,
    **kwargs,
  ):
    self.attrs = widget.attrs
    # kwargs can supersede attrs
    self.attrs.update(kwargs)
    self.widget = widget
    self.can_add_related = can_add_related
    self.can_change_related = can_change_related
    self.add_url = add_url
    self.add_title = add_title
    self.change_url = change_url
    self.change_title = change_title

  def get_context(self, name: str, value: Any, attrs: dict[str, Any] | None) -> dict[str, Any]:
    context = {
      "rendered_widget": self.widget.render(name, value, attrs),
      "is_hidden": self.is_hidden,
      "name": self.attrs["name"] if "name" in self.attrs else name,
      "can_add_related": self.can_add_related,
      "can_change_related": self.can_change_related,
      "add_url": self.add_url,
      "change_url": self.change_url,
      "add_title": self.add_title,
      "change_title": self.change_title,
    }
    return context

  def value_from_datadict(self, data, files, name):
    return self.widget.value_from_datadict(data, files, name)

  def value_omitted_from_data(self, data, files, name):
    return self.widget.value_omitted_from_data(data, files, name)

  def id_for_label(self, id_):
    return self.widget.id_for_label(id_)
