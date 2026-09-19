"""Design value -> literal CSS declarations for MJML/email rendering.

This is the email-side counterpart to :mod:`wagtail_daisIE.base_blocks.css`.
The class builders in ``css.py`` emit Tailwind/DaisyUI utility class names for
the web; email clients do not support classes or CSS custom properties, so the
builders here resolve the *same design value dicts* into ordered
``{css_property: literal_value}`` mappings.

Two things are resolved that the web does not need at build time:

* **Colours** — ``bg-primary`` / ``text-[#0080ff]`` / raw hex are turned into
  literal 6-digit hex using the active :class:`DaisyUITheme`.
* **Fonts** — ``font-heading`` / a role / a custom name is turned into the
  theme font family's ``css_value`` stack.

The builders never touch the database at import time; the theme is passed in at
render time (see ``EmailTemplate.get_theme``).
"""

import re


_SPACING_STEPS = {
    "0": "0",
    "px": "1px",
}
for _n in (
    0.5,
    1,
    1.5,
    2,
    2.5,
    3,
    3.5,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    14,
    16,
    20,
    24,
    28,
    32,
    36,
    40,
    44,
    48,
    52,
    56,
    60,
    64,
    72,
    80,
    96,
):
    _suffix = f"{_n:g}"
    _SPACING_STEPS[_suffix] = f"{_n * 0.25:g}rem"

# Tailwind v4 font sizes. ``2xl``..``9xl`` are the framework defaults;
# ``10xl``..``42xl`` are declared in the package's ``source.css`` ``@theme``.
_FONT_SIZES = {
    "xs": "0.75rem",
    "sm": "0.875rem",
    "md": "1rem",
    "lg": "1.125rem",
    "xl": "1.25rem",
    "2xl": "1.5rem",
    "3xl": "1.875rem",
    "4xl": "2.25rem",
    "5xl": "3rem",
    "6xl": "3.75rem",
    "7xl": "4.5rem",
    "8xl": "6rem",
    "9xl": "8rem",
}
for _n in range(10, 43):
    _FONT_SIZES[f"{_n}xl"] = f"{8.25 + 0.25 * (_n - 10)}rem"

_FONT_WEIGHTS = {
    "thin": "100",
    "extralight": "200",
    "light": "300",
    "normal": "400",
    "medium": "500",
    "semibold": "600",
    "bold": "700",
    "extrabold": "800",
    "black": "900",
}

_LINE_HEIGHTS = {
    "none": "1",
    "tight": "1.25",
    "snug": "1.375",
    "normal": "1.5",
    "relaxed": "1.625",
    "loose": "2",
}

_LETTER_SPACING = {
    "tighter": "-0.05em",
    "tight": "-0.025em",
    "normal": "0",
    "wide": "0.025em",
    "wider": "0.05em",
    "widest": "0.1em",
}

_RADII = {
    "xs": "0.125rem",
    "sm": "0.25rem",
    "md": "0.375rem",
    "lg": "0.5rem",
    "xl": "0.75rem",
    "2xl": "1rem",
    "3xl": "1.5rem",
    "4xl": "2rem",
    "full": "9999px",
}

_SHADOWS = {
    "2xs": "0 1px rgb(0 0 0 / 0.05)",
    "xs": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    "sm": "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
    "md": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    "lg": ("0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)"),
    "xl": ("0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)"),
    "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)",
}

# daisyUI button size presets, approximately: (font-size, inner-padding).
_BUTTON_SIZES = {
    "xs": ("0.6875rem", "0.25rem 0.5rem"),
    "sm": ("0.75rem", "0.5rem 1rem"),
    "md": ("0.875rem", "0.5rem 1rem"),
    "lg": ("1.125rem", "0.75rem 1rem"),
    "xl": ("1.375rem", "0.75rem 1rem"),
}

_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
_CLASS_HEX = re.compile(r"\[(#[0-9a-fA-F]{3,8})\]")

_COLOR_PREFIXES = ("bg-", "text-", "border-")
_GENERIC_FONTS = {
    "sans-serif",
    "serif",
    "monospace",
    "cursive",
    "fantasy",
    "system-ui",
    "ui-sans-serif",
    "ui-serif",
    "ui-monospace",
    "emoji",
    "math",
    "fangsong",
}


def flatten_hex(value):
    """Reduce ``#rrggbbaa``/``#rgba`` to the 6-digit form email clients accept."""
    if not isinstance(value, str) or not value.startswith("#"):
        return value
    body = value[1:]
    if len(body) == 8:
        return f"#{body[:6]}"
    if len(body) == 4:
        return f"#{body[:3]}"
    return value


def _theme_palette(theme):
    if theme is None:
        return {}
    from wagtail_daisIE.utils import get_draftail_color_palette

    palette = {}
    for entry in get_draftail_color_palette(theme):
        if entry.get("value"):
            palette[entry["key"]] = flatten_hex(entry["value"])
    return palette


def resolve_color(raw, theme=None):
    """Resolve a design colour value to a literal CSS colour, or ``None``.

    Accepts raw hex (``#0080ff``), raw swatch hex (``#0080ffaa``), arbitrary
    Tailwind colour utilities (``bg-[#0080ff]``) and daisyUI tokens
    (``bg-primary``, ``text-primary-content``).
    """
    if not raw:
        return None
    match = _CLASS_HEX.search(raw)
    if match:
        return flatten_hex(match.group(1))
    if raw.startswith("#"):
        return flatten_hex(raw)

    token = raw
    for prefix in _COLOR_PREFIXES:
        if token.startswith(prefix):
            token = token[len(prefix) :]
            break
    if token in ("transparent", "inherit", "currentColor", "current"):
        return token
    return _theme_palette(theme).get(token.replace("-", "_"))


def resolve_font_family(raw, theme=None):
    """Resolve a font family design value to a literal CSS font stack."""
    if not raw:
        return None
    token = raw[5:] if raw.startswith("font-") else raw
    if token in _GENERIC_FONTS:
        return token
    if theme is None:
        return token
    fonts = getattr(theme, "fonts", None)
    if fonts is None:
        return token
    if hasattr(fonts, "first") and not hasattr(fonts, "role"):
        fonts = fonts.first()
    if fonts is None:
        return token
    for family in fonts.font_families.all():
        if str(family) == token:
            return family.css_value
    return token


def _spacing(raw):
    if not raw:
        return None
    return _SPACING_STEPS.get(raw.rsplit("-", 1)[-1])


def _dimension(raw):
    """Resolve a width/height utility value (``w-4``, ``h-full``, ``w-px``)."""
    if not raw:
        return None
    suffix = raw.rsplit("-", 1)[-1]
    if suffix in ("full", "screen"):
        return "100%"
    if suffix in _SPACING_STEPS:
        return _SPACING_STEPS[suffix]
    return None


def _size_declarations(raw, width=True, height=True):
    if not raw:
        return {}
    suffix = raw.split("-", 1)[-1]
    if "-" not in raw:
        return {}
    out = {}
    if suffix in _SPACING_STEPS:
        value = _SPACING_STEPS[suffix]
        if width:
            out["width"] = value
        if height:
            out["height"] = value
    return out


def _font_size(raw):
    if not raw:
        return None
    return _FONT_SIZES.get(raw.split("-", 1)[-1])


def _font_weight(raw):
    if not raw:
        return None
    return _FONT_WEIGHTS.get(raw.split("-", 1)[-1])


def _text_align(raw):
    if not raw:
        return None
    suffix = raw.split("-", 1)[-1]
    if suffix in ("left", "center", "right", "justify"):
        return suffix
    return None


def _line_height(raw):
    if not raw:
        return None
    return _LINE_HEIGHTS.get(raw.split("-", 1)[-1])


def _letter_spacing(raw):
    if not raw:
        return None
    return _LETTER_SPACING.get(raw.split("-", 1)[-1])


def _radius(raw):
    if not raw:
        return None
    return _RADII.get(raw.split("-", 1)[-1])


def _shadow(raw):
    if not raw:
        return None
    return _SHADOWS.get(raw.split("-", 1)[-1])


def build_size_style(value, theme=None):
    if not value:
        return {}
    out = {}
    out.update(_size_declarations(value.get("size")))
    width = value.get("width")
    if isinstance(width, dict):
        for key, prop in (
            ("width", "width"),
            ("min_width", "min-width"),
            ("max_width", "max-width"),
        ):
            resolved = _dimension(width.get(key))
            if resolved:
                out[prop] = resolved
    height = value.get("height")
    if isinstance(height, dict):
        for key, prop in (
            ("height", "height"),
            ("min_height", "min-height"),
            ("max_height", "max-height"),
        ):
            resolved = _dimension(height.get(key))
            if resolved:
                out[prop] = resolved
    return out


def build_spacing_style(value, theme=None):
    # CSS ``gap`` has no MJML attribute; spacing is handled by the calling
    # layout block (as padding on columns) rather than here.
    return {}


def build_background_style(value, theme=None):
    if not value:
        return {}
    out = {}
    color = resolve_color(value.get("bg_color"), theme)
    if color:
        out["background-color"] = color
    mode = value.get("bg_image")
    if mode == "bg-cover":
        out["background-size"] = "cover"
    elif mode == "bg-contain":
        out["background-size"] = "contain"
    return out


def build_border_style(value, theme=None):
    if not value:
        return {}
    width = value.get("border_width")
    if not width or width <= 0:
        return {}
    style = value.get("border_style") or "solid"
    color = resolve_color(value.get("border_color"), theme) or "#000000"
    return {"border": f"{width}px {style} {color}"}


def build_padding_style(value, theme=None):
    if not value:
        return {}
    out = {}
    all_value = _spacing(value.get("all_padding"))
    if all_value:
        out["padding"] = all_value
    for side in ("top", "right", "bottom", "left"):
        resolved = _spacing(value.get(side))
        if resolved:
            out[f"padding-{side}"] = resolved
    return out


def build_margin_style(value, theme=None):
    if not value:
        return {}
    out = {}
    all_value = value.get("all_margins")
    if all_value == "auto":
        out["margin"] = "auto"
    elif _spacing(all_value):
        out["margin"] = _spacing(all_value)
    for side in ("top", "right", "bottom", "left"):
        raw = value.get(side)
        if raw == "auto":
            out[f"margin-{side}"] = "auto"
        elif _spacing(raw):
            out[f"margin-{side}"] = _spacing(raw)
    return out


def build_box_style(value, theme=None):
    if not value:
        return {}
    out = {}
    radius = _radius(value.get("rounded"))
    if radius:
        out["border-radius"] = radius
    shadow = _shadow(value.get("shadow"))
    if shadow:
        out["box-shadow"] = shadow
    return out


def build_typography_style(value, theme=None):
    if not value:
        return {}
    out = {}
    color = resolve_color(value.get("text_color"), theme)
    if color:
        out["color"] = color
    font = resolve_font_family(value.get("font_family"), theme)
    if font:
        out["font-family"] = font
    for raw, prop, resolver in (
        (value.get("font_size"), "font-size", _font_size),
        (value.get("font_weight"), "font-weight", _font_weight),
        (value.get("text_align"), "text-align", _text_align),
        (value.get("line_height"), "line-height", _line_height),
        (value.get("letter_spacing"), "letter-spacing", _letter_spacing),
    ):
        resolved = resolver(raw)
        if resolved:
            out[prop] = resolved
    return out


def build_button_state_style(value, theme=None):
    """Declarations for a single button state (normal/hover/active)."""
    if not value:
        return {}
    token = value.get("color") or ""
    if token.startswith("btn-"):
        token = token[4:]
    base = resolve_color(token, theme) if token else None
    content = resolve_color(f"{token.replace('-content', '')}-content", theme)

    style = value.get("style") or ""
    out = {}
    if style == "btn-outline" and base:
        out["background-color"] = "transparent"
        out["border"] = f"1px solid {base}"
        out["color"] = base
    elif style == "btn-soft" and base:
        out["background-color"] = base
        out["color"] = content or base
    elif base:
        out["background-color"] = base
        if content:
            out["color"] = content

    size = (value.get("size") or "").removeprefix("btn-")
    if size in _BUTTON_SIZES:
        font_size, padding = _BUTTON_SIZES[size]
        out["font-size"] = font_size
        out["inner-padding"] = padding
    return out


def build_button_style(value, theme=None):
    if not value:
        return {}
    return build_button_state_style(value.get("normal"), theme)


def build_table_style(value, theme=None):
    # Table rendering is deferred; the registry knows the component but the
    # design -> attribute mapping is added with the ``EmailTableBlock``.
    return {}


_DESIGN_STYLE_BUILDERS = {
    "size": build_size_style,
    "spacing": build_spacing_style,
    "background": build_background_style,
    "border": build_border_style,
    "padding": build_padding_style,
    "margin": build_margin_style,
    "box": build_box_style,
    "typography": build_typography_style,
    "button_appearance": build_button_style,
    "table_appearance": build_table_style,
}


def build_design_style(value, theme=None):
    """Aggregate a design value into ordered ``{css_property: value}`` mappings."""
    if not value:
        return {}
    out = {}
    for key, builder in _DESIGN_STYLE_BUILDERS.items():
        if key in value:
            out.update(builder(value.get(key), theme))
    return out


def style_to_css(declarations):
    """Serialise a declaration mapping into an inline CSS string."""
    return "; ".join(f"{prop}: {value}" for prop, value in declarations.items())


def split_style(declarations, attr_map):
    """Split declarations into MJML attributes and CSS leftovers.

    ``attr_map`` maps canonical CSS property -> MJML attribute name. Anything
    not in the map is returned as leftover CSS (to be emitted through
    ``css-class`` + ``mj-style``).
    """
    attrs = {}
    leftover = {}
    for prop, value in declarations.items():
        target = attr_map.get(prop)
        if target:
            attrs[target] = value
        else:
            leftover[prop] = value
    return attrs, leftover
