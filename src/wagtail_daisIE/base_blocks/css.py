"""Pure CSS class builders for the design blocks.

Each builder takes the raw ``value`` dict of a design child block and returns
the space-separated list of utility classes it maps to. The builders are used
both by the individual design blocks (in their :meth:`get_context`) and by
:func:`build_design_css` to aggregate the whole :class:`DesignBlock` value into
the ``block_css`` template variable.
"""

from .utils import build_border_width, build_class


def merge_block_css(parent_context, own):
    """Combine inherited ``block_css`` from ``parent_context`` with ``own``.

    Blocks are reused inside both pages and menus. A menu may inject default
    ``block_css`` through the parent context (see ``MenuItemDesignBlock``), so
    each design block prepends whatever it inherited before appending its own
    classes. Per-block settings therefore come last and win where CSS order
    allows.
    """
    inherited = (parent_context or {}).get("block_css", "")
    return build_class(inherited, own)


def build_size_css(value):
    """CSS classes for a size block (``InlineSizeBlock``/``BlockSizeBlock``).

    Width and height are nested struct values, so both the plain field values
    and the nested sub-fields are handled.
    """
    if not value:
        return ""
    width = value.get("width", "")
    height = value.get("height", "")
    if isinstance(width, dict):
        width = build_class(
            width.get("width", ""),
            width.get("min_width", ""),
            width.get("max_width", ""),
        )
    if isinstance(height, dict):
        height = build_class(
            height.get("height", ""),
            height.get("min_height", ""),
            height.get("max_height", ""),
        )
    return build_class(
        value.get("size", ""),
        width,
        height,
    )


def build_media_size_css(value):
    if not value:
        return ""
    size_css = build_size_css(value)
    aspect = value.get("aspect", "")
    return build_class(size_css, aspect)


def build_spacing_css(value):
    if not value:
        return ""
    return build_class(
        value.get("all", ""),
        value.get("horizontal", ""),
        value.get("vertical", ""),
    )


def build_background_css(value):
    if not value:
        return ""
    return build_class(
        value.get("bg_color", ""),
        value.get("bg_image", ""),
    )


def build_border_css(value):
    if not value:
        return ""
    border_width = value.get("border_width")
    if not border_width or border_width <= 0:
        return ""
    return build_class(
        build_border_width(border_width),
        value.get("border_color", ""),
        value.get("border_style", ""),
    )


def build_padding_css(value):
    if not value:
        return ""
    return build_class(
        value.get("all_padding", ""),
        value.get("top", ""),
        value.get("right", ""),
        value.get("bottom", ""),
        value.get("left", ""),
    )


def build_margin_css(value):
    if not value:
        return ""
    return build_class(
        value.get("all_margins", ""),
        value.get("top", ""),
        value.get("right", ""),
        value.get("bottom", ""),
        value.get("left", ""),
    )


def build_box_css(value):
    if not value:
        return ""
    return build_class(
        value.get("rounded", ""),
        value.get("shadow", ""),
    )


def build_typography_css(value):
    if not value:
        return ""
    font_family = value.get("font_family", "")
    if font_family and not font_family.startswith("font-"):
        font_family = f"font-{font_family}"
    return build_class(
        value.get("text_color", ""),
        font_family,
        value.get("font_size", ""),
        value.get("font_weight", ""),
        value.get("text_align", ""),
        value.get("line_height", ""),
        value.get("letter_spacing", ""),
    )


def build_button_state_css(value, variant=""):
    if not value:
        return ""
    prefix = f"{variant}:" if variant else ""
    color = value.get("color")
    style = value.get("style")
    size = value.get("size")
    behavior = value.get("behavior")
    modifier = value.get("modifier")

    return build_class(
        *(f"{prefix}{v}" for v in [color, style, size, behavior, modifier] if v)
    )


def build_button_css(value):
    if not value:
        return ""
    normal = value.get("normal")
    hover = value.get("hover")
    active = value.get("active")
    return build_class(
        "btn",
        build_button_state_css(normal),
        build_button_state_css(hover, variant="hover"),
        build_button_state_css(active, variant="active"),
    )


_DESIGN_BUILDERS = {
    "size": build_size_css,
    "spacing": build_spacing_css,
    "background": build_background_css,
    "border": build_border_css,
    "padding": build_padding_css,
    "margin": build_margin_css,
    "box": build_box_css,
    "typography": build_typography_css,
    "button_appearance": build_button_css,
}


def build_design_css(value):
    """Aggregate the CSS classes of a design block value into one string.

    Only the design groups present on the block are consulted, so this works
    for every design variant (``DesignBlock``, ``InlineDesignBlock``,
    ``TypographyDesignBlock``, ``SpacedDesignBlock`` and friends). Groups the
    block does not define (for example ``button_appearance`` on a text block)
    contribute nothing.
    """
    if not value:
        return ""
    return build_class(
        *(
            builder(value.get(key))
            for key, builder in _DESIGN_BUILDERS.items()
            if key in value
        )
    )
