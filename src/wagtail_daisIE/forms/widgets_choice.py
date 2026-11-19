"""DaisyUI-styled checkbox and radio group widgets."""

from __future__ import annotations

from django import forms


class DaisieChoiceWidgetMixin:
    template_name = "wagtail_daisIE/forms/widgets/choice_group.html"
    option_template_name = "wagtail_daisIE/forms/widgets/choice_option.html"

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if getattr(self, "option_layout_configured", False):
            option["option_layout_configured"] = True
            option["option_input_css"] = getattr(self, "option_input_css", "")
            option["option_label_css"] = getattr(self, "option_label_css", "")
            option["option_input_hidden"] = getattr(self, "option_input_hidden", False)
            option["option_label_hidden"] = getattr(self, "option_label_hidden", False)
            if option["option_label_hidden"]:
                option["attrs"]["aria-label"] = str(label)
        return option


class DaisieCheckboxSelectMultiple(
    DaisieChoiceWidgetMixin, forms.CheckboxSelectMultiple
):
    pass


class DaisieRadioSelect(DaisieChoiceWidgetMixin, forms.RadioSelect):
    pass


__all__ = [
    "DaisieCheckboxSelectMultiple",
    "DaisieRadioSelect",
]
