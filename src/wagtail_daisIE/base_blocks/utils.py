import re

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from wagtail_daisIE.choices import ASPECT_RATIO_CHOICES


def build_class(*values):
    return " ".join(v for v in values if v)


def build_border_width(value: int | None) -> str:
    if value is None or value <= 0:
        return ""
    if value == 1:
        return "border"
    return f"border-{value}"


def validate_aspect(value):
    if not value:
        return
    if not isinstance(value, str):
        raise ValidationError(
            _("Invalid aspect ratio. Expected one of: %(choices)s."),
            code="wagtail_daisIE.invalid_aspect_ratio",
            params={"choices": ", ".join(ASPECT_RATIO_CHOICES)},
        )

    match = re.fullmatch(r"(\d+):(\d+)", value)
    if not match and value.lower() not in ("auto", "square", "video"):
        raise ValidationError(
            _("Invalid aspect ratio. Expected one of: %(choices)s."),
            code="wagtail_daisIE.invalid_aspect_ratio",
            params={"choices": ", ".join(ASPECT_RATIO_CHOICES)},
        )


# Shared choice builder for font families
def _theme_font_families(theme):
    if theme is None:
        return []
    fonts = getattr(theme, "fonts", None)
    if fonts is None:
        return []
    # ``theme.fonts`` may be a manager (call .first()) or the related
    # DaisyUIThemeFonts instance directly.
    if hasattr(fonts, "first") and not isinstance(fonts, models.Model):
        fonts = fonts.first()
    if fonts is None:
        return []
    families = getattr(fonts, "font_families", None)
    if families is None:
        return []
    return list(families.all())


def build_font_family_choices(theme, raw=False):
    """
    Return ``[(value, label), ...]`` for ``theme``'s font families.

    * ``raw=False`` → value is the role (or the ``name`` for custom roles);
      this is what ``DaisyUIFontFamilyWidget`` submits.
    * ``raw=True`` → value is the family's ``css_value``; this is what
      ``DaisyUIRawFontFamilyWidget`` submits.
    """
    choices = []
    for family in _theme_font_families(theme):
        value = family.css_value if raw else str(family)
        label = str(family).capitalize()
        if value:
            choices.append((value, label))
    return choices
