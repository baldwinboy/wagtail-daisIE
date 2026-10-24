"""DaisyUI-styled checkbox and radio group widgets."""

from __future__ import annotations

from django import forms


class DaisieChoiceWidgetMixin:
    template_name = "wagtail_daisIE/forms/widgets/choice_group.html"
    option_template_name = "wagtail_daisIE/forms/widgets/choice_option.html"


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
