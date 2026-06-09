from django import forms

from .widgets import DaisyUISize, DaisyUISizeUnitChoices, DaisyUISizeWidget


class DaisyUISizeFormField(forms.MultiValueField):
    widget = DaisyUISizeWidget

    def __init__(self, **kwargs):
        kwargs.pop("max_length", None)
        fields = (
            forms.FloatField(min_value=0),  # or allow negative if needed
            forms.ChoiceField(choices=DaisyUISizeUnitChoices.choices),
        )
        # We need to set require_all_fields to True so that if one part is missing,
        # the whole field is considered incomplete.
        kwargs.setdefault("require_all_fields", True)
        super().__init__(fields=fields, **kwargs)

    def compress(self, data_list):
        """Combine the two sub-values back into a DaisyUISize object."""
        if data_list:
            number, unit = data_list
            if number is not None and unit in dict(DaisyUISizeUnitChoices.choices):
                return DaisyUISize(float(number), unit)
        return None
