"""Widgets for context bindings."""

from __future__ import annotations

from django import forms


class ContextBindingValueWidget(forms.Widget):
    """Render a context binding's hidden value plus a display placeholder."""

    template_name = "wagtail_daisIE/admin/context_binding_value_widget.html"

    def format_value(self, value):
        if isinstance(value, dict):
            return {
                "id": str(value.get("id") or ""),
                "title": str(value.get("title") or ""),
                "edit_url": str(value.get("edit_url") or ""),
            }
        return {"id": str(value or ""), "title": "", "edit_url": ""}

    @property
    def media(self):
        return forms.Media(
            js=[
                "wagtail_daisIE/js/widget_definition.js",
                "wagtail_daisIE/js/context_binding_value.js",
            ]
        )

    def value_from_datadict(self, data, files, name):
        return data.get(name)
