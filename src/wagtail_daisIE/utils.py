from django.utils.translation import gettext_lazy as _


class DefaultSwatchColors:
    primary = "#422ad5ff"
    primary_content = "#e0e7ffff"
    secondary = "#f43098ff"
    secondary_content = "#f9e4f0ff"
    accent = "#00d3bbff"
    accent_content = "#084d49ff"
    neutral = "#0b0809ff"
    neutral_content = "#e7e3e4ff"
    base_100 = "#ffffffff"
    base_200 = "#f8f8f8ff"
    base_300 = "#eeeeeeff"
    base_content = "#1b1718ff"
    info = "#00bafeff"
    info_content = "#042e49ff"
    success = "#00d390ff"
    success_content = "#004c39ff"
    warning = "#fcb700ff"
    warning_content = "#793205ff"
    error = "#ff637dff"
    error_content = "#4d0218ff"


DEFAULT_SWATCH_COLORS = DefaultSwatchColors()


def get_draftail_color_palette(theme=None):
    """
    Return the default DaisyUI theme's colours as a
    draftail_text_utils-compatible colour palette list.

    Returns a list of dicts with "key", "label", and "value" (hex) keys,
    or an empty list if no default theme exists.
    """
    from .models import DaisyUITheme

    try:
        if theme is None:
            theme = DaisyUITheme.objects.filter(default=True).first()

        if theme:
            colors = theme.colors.first()
            if not colors:
                colors = DEFAULT_SWATCH_COLORS
        else:
            colors = DEFAULT_SWATCH_COLORS
    except Exception:
        colors = DEFAULT_SWATCH_COLORS

    color_fields = [
        ("primary", _("Primary")),
        ("primary_content", _("Primary content")),
        ("secondary", _("Secondary")),
        ("secondary_content", _("Secondary content")),
        ("accent", _("Accent")),
        ("accent_content", _("Accent content")),
        ("neutral", _("Neutral")),
        ("neutral_content", _("Neutral content")),
        ("base_100", _("Base")),
        ("base_200", _("Base Dark")),
        ("base_300", _("Base Darker")),
        ("base_content", _("Base content")),
        ("info", _("Info")),
        ("info_content", _("Info content")),
        ("success", _("Success")),
        ("success_content", _("Success content")),
        ("warning", _("Warning")),
        ("warning_content", _("Warning content")),
        ("error", _("Error")),
    ]

    return [
        {
            "key": field_name,
            "label": label,
            "value": getattr(colors, field_name)[:7],
        }
        for field_name, label in color_fields
    ]


def get_draftail_font_families(theme=None):
    """
    Return the default DaisyUI theme's font families as a
    draftail_text_utils-compatible font families list.

    Returns a list of dicts with "label" and "value" keys,
    or an empty list if no default theme exists.
    """
    from .models import DaisyUITheme

    if not theme:
        try:
            theme = DaisyUITheme.objects.filter(default=True).first()
            if not theme:
                return []
        except Exception:
            return []

    fonts = theme.fonts.first()
    if not fonts:
        return []

    font_families = fonts.font_families.all()
    if not font_families:
        return []

    return [
        {"label": _(family.__str__.capitalize()), "value": family.css_value}
        for family in font_families
    ]


def get_draftail_font_urls(theme=None):
    """
    Return the default DaisyUI theme's font CDN URLs as a
    draftail_text_utils-compatible font URLs list.

    Returns a list of URL strings, or an empty list if no default theme exists.
    """
    from .models import DaisyUITheme

    if not theme:
        try:
            theme = DaisyUITheme.objects.filter(default=True).first()
            if not theme:
                return []
        except Exception:
            return []
    return list(theme.font_cdns.values_list("url", flat=True))


def get_draftail_font_sizes():
    """
    Return a draftail_text_utils-compatible font sizes configuration
    derived from the default DaisyUI theme.

    Returns a dict with "MIN", "MAX", "STEP", and "PRESETS" keys,
    or None to let draftail_text_utils use its defaults.
    """
    return None
