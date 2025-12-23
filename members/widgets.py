from typing import Any
from django.forms import Widget


class FieldLinkWrapper(Widget):
    template_name = "widgets/wrap_create_link.html"

    def __init__(
        self, widget, can_add_related=False, can_change_related=False, **kwargs
    ):
        self.attrs = widget.attrs
        # kwargs can supersede attrs
        self.attrs.update(kwargs)
        self.widget = widget
        self.can_add_related = can_add_related
        self.can_change_related = can_change_related

    def get_context(
        self, name: str, value: Any, attrs: dict[str, Any] | None
    ) -> dict[str, Any]:
        context = {
            "rendered_widget": self.widget.render(name, value, attrs),
            "is_hidden": self.is_hidden,
            "name": self.attrs["name"] if "name" in self.attrs else name,
            "can_add_related": self.can_add_related,
            "can_change_related": self.can_change_related,
        }
        return context

    def value_from_datadict(self, data, files, name):
        return self.widget.value_from_datadict(data, files, name)

    def value_omitted_from_data(self, data, files, name):
        return self.widget.value_omitted_from_data(data, files, name)

    def id_for_label(self, id_):
        return self.widget.id_for_label(id_)
