import re

from colorfield.widgets import ColorWidget
from django import forms
from django.db import models
from django.forms import ValidationError, widgets
from django.utils.translation import gettext_lazy as _


class DaisyUISizeUnitChoices(models.TextChoices):
    PX = "px", _("px (Pixels)")
    EM = "em", _("em (Parent element's font size)")
    REM = "rem", _("rem (Root element's font size)")
    VW = "vw", _("vw (Viewport width)")
    VH = "vh", _("vh (Viewport height)")
    PT = "pt", _("pt (Points)")
    PC = "pc", _("pc (Picas)")
    IN = "in", _("in (Inches)")
    CM = "cm", _("cm (Centimeters)")
    MM = "mm", _("mm (Millimeters)")
    Q = "q", _("q (Quarters)")


class DaisyUISize:
    def __init__(self, value: float, unit: str):
        self.value = value
        self.unit = unit

    def __str__(self):
        return f"{self.value}{self.unit}"

    def __repr__(self):
        return f"DaisyUISize({self.value!r}, {self.unit!r})"

    def __len__(self):
        return len(str(self))

    def __eq__(self, other):
        if isinstance(other, DaisyUISize):
            return self.value == other.value and self.unit == other.unit
        return NotImplemented

    @classmethod
    def from_value(cls, value):
        if isinstance(value, DaisyUISize) or value is None:
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None

            # optional whitespace, and a unit (letters)
            match = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*([a-zA-Z]+)", value)
            if not match:
                raise ValidationError(
                    _(
                        'Invalid CSS size format. Expected a number followed by a unit, e.g. "10px".'
                    ),
                    code="wagtail_daisIE.invalid_size_format",
                )

            value, unit = match.groups()

            if unit not in DaisyUISizeUnitChoices.values:
                raise ValidationError(
                    _("Invalid CSS size unit. Expected one of: %(choices)s"),
                    code="wagtail_daisIE.invalid_size_unit",
                    params={"choices": ", ".join(DaisyUISizeUnitChoices.values)},
                )

            try:
                value = float(value)
            except ValueError as exc:
                raise ValidationError(
                    _(
                        'Invalid CSS size value. Expected a number followed by a unit, e.g. "10px".'
                    ),
                    code="wagtail_daisIE.invalid_size_value",
                ) from exc

            return DaisyUISize(float(value), unit)


class DaisyUISizeWidget(forms.MultiWidget):
    template_name = "wagtail_daisIE/admin/daisyui_size_widget.html"

    def __init__(self, attrs=None):
        _widgets = (
            widgets.NumberInput(attrs={"step": "any", "placeholder": "Value"}),
            widgets.Select(choices=DaisyUISizeUnitChoices.choices),
        )
        super().__init__(_widgets, attrs)

    def decompress(self, value):
        """
        Convert a single DaisyUISize value into a list [number, unit]
        for the two sub-widgets.
        """
        if value is None:
            return [None, None]
        if isinstance(value, DaisyUISize):
            return [value.value, value.unit]
        if isinstance(value, str):
            obj = DaisyUISize.from_value(value)
            if obj:
                return [obj.value, obj.unit]
        return [None, None]


class DaisyUIColorWidget(ColorWidget):
    def get_context(self, name, value, attrs=None):
        context = super().get_context(name, value, attrs)
        options = context.get("data_coloris_options", {})
        options["format"] = "hexa"
        options["alpha"] = True
        options["forceAlpha"] = True
        context["data_coloris_options"] = options
        return context
