from django import forms
from django.urls import NoReverseMatch, reverse

from .registry import enabled_providers, render_icon


class IconChooserWidget(forms.TextInput):
    """Text input backed by a searchable, provider-aware icon picker."""

    template_name = "wagtail_daisIE/admin/daisyui_icon_widget.html"

    def get_context(self, name, value, attrs=None):
        context = super().get_context(name, value, attrs)
        value = value or ""
        try:
            search_url = reverse("wagtail_daisIE:icon_search")
        except NoReverseMatch:
            search_url = ""
        context["widget"].update(
            {
                "current_value": value,
                "current_preview": render_icon(value),
                "icon_search_url": search_url,
                "sources": [
                    {
                        "prefix": provider.prefix,
                        "label": str(provider.label),
                        "kind": provider.kind,
                    }
                    for provider in enabled_providers()
                ],
            }
        )
        return context
