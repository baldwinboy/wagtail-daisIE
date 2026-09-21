"""Forms fields for selecting an instance of a binding's model.

The value is the selected object's primary key; the model is implied by the
context-binding key, so no separate model chooser is needed.
"""

from __future__ import annotations

from django import forms


def _coerce(value):
    """Return an integer primary key, or ``None``."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class DynamicInstanceWidget(forms.Widget):
    """Renders an inline search + select for the bound model's instances."""

    template_name = "wagtail_daisIE/admin/binding_instance_widget.html"

    def get_context(self, name, value, attrs):
        from django.urls import NoReverseMatch, reverse

        context = super().get_context(name, value, attrs)
        try:
            endpoint = reverse("wagtail_daisIE:dynamic_object_options")
        except NoReverseMatch:  # pragma: no cover - admin not mounted
            endpoint = ""
        context["daisie_widget"] = {
            "name": name,
            "id": context["widget"]["attrs"].get("id") or name,
            "object_id": _coerce(value),
            "endpoint": endpoint,
            "attrs": context["widget"]["attrs"],
        }
        return context

    def value_from_datadict(self, data, files, name):
        return data.get(name, "")


class DynamicInstanceField(forms.Field):
    """A form field storing the selected instance's primary key."""

    widget = DynamicInstanceWidget

    def prepare_value(self, value):
        return _coerce(value)

    def to_python(self, value):
        return _coerce(value)

    def has_changed(self, initial, data):
        return _coerce(initial) != _coerce(data)
