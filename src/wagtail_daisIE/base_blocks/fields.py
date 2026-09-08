import re

from django import forms
from wagtail import blocks

from ..context import get_current_theme
from .utils import build_font_family_choices


def resolve_font_family_theme():
    """Return the theme whose font families should populate the picker.

    Prefers the theme currently being edited (set by the admin hooks via
    :func:`~wagtail_daisIE.context.get_current_theme`), falling back to the
    default theme so the picker and previews still work. Resolved lazily at
    request time to avoid querying the database at import time.
    """
    theme = get_current_theme()
    if theme is not None:
        return theme
    try:
        from ..models import DaisyUITheme

        return DaisyUITheme.objects.filter(default=True).first()
    except Exception:
        return None


class SwatchChoiceField(forms.ChoiceField):
    """
    ChoiceField that also accepts arbitrary colour values beyond the preset
    palette: DaisyUI utility classes such as ``bg-[#0080ff]`` and raw hex
    colours such as ``#0080ff`` (used by the raw swatch widgets).
    """

    CUSTOM_CLASS_PATTERN = re.compile(r"(?:bg|text|border)-\[#[0-9a-fA-F]{3,8}\]")
    RAW_HEX_PATTERN = re.compile(r"#[0-9a-fA-F]{3,8}")

    def validate(self, value):
        if value not in ("", None) and isinstance(value, str):
            if self.CUSTOM_CLASS_PATTERN.fullmatch(value):
                return
            if self.RAW_HEX_PATTERN.fullmatch(value):
                return
        super().validate(value)


class ColorChoiceBlock(blocks.ChoiceBlock):
    """ChoiceBlock for colour swatches that accepts custom colours too."""

    def get_field(self, **kwargs):
        return SwatchChoiceField(**kwargs)


class FontFamilyChoiceBlock(blocks.ChoiceBlock):
    """
    ``ChoiceBlock`` whose options come from the theme being edited.

    The stored value is the font family role (or the custom name), matching
    the ``--font-<role>`` custom properties emitted by the theme font tag.
    Choices are resolved lazily in ``get_form_state``/``render_form`` so no
    database access happens at import time.

    Parameters
    ----------
    raw:
        If ``True`` the stored value is the family's full ``css_value``.
    theme_getter:
        Optional callable returning a ``DaisyUITheme``. Defaults to
        :func:`resolve_font_family_theme`.
    """

    def __init__(self, *args, raw=False, theme_getter=None, **kwargs):
        self.raw = raw
        self.theme_getter = theme_getter or resolve_font_family_theme

        # Start with empty choices; the choices are filled in per request.
        kwargs.setdefault("choices", [])
        super().__init__(*args, **kwargs)

    def _resolved_choices(self):
        theme = self.theme_getter() if self.theme_getter else None
        return build_font_family_choices(theme, raw=self.raw)

    def get_form_state(self, value):
        # Assigning ``field.choices`` also updates ``field.widget.choices``
        # (Django's ChoiceField._set_choices does this).
        self.field.choices = self._resolved_choices()
        return super().get_form_state(value)

    def render_form(self, *args, **kwargs):
        self.field.choices = self._resolved_choices()
        return super().render_form(*args, **kwargs)

    def deconstruct(self):
        """
        Deconstruct as a plain ``ChoiceBlock`` — the dynamic choices and the
        theme-aware widget are not migration-serialisable.
        """
        _path, args, kwargs = super().deconstruct()
        kwargs.pop("choices", None)
        kwargs.pop("raw", None)
        kwargs.pop("theme_getter", None)
        return ("wagtail.blocks.ChoiceBlock", args, kwargs)
