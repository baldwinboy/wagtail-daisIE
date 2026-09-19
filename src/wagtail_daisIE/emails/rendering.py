"""Render an :class:`~wagtail_daisIE.emails.models.EmailTemplate` to MJML.

Rendering happens in two passes because ``mj-style`` can only live in
``<mj-head>`` (rendered before the body) while the CSS rules are only known
once the body blocks have run. The first pass renders the body and fills a
shared style registry; the second renders the full document with both.
"""

from django.template.loader import render_to_string

from ..base_blocks.design import PageDesignBlock
from ..base_blocks.mjml import flatten_hex, split_style
from ..utils import get_draftail_color_palette
from .mjml import ATTR_MAPS, CATEGORY_TAGS


def _palette(theme):
    if theme is None:
        return {}
    return {
        entry["key"]: flatten_hex(entry["value"])
        for entry in get_draftail_color_palette(theme)
        if entry.get("value")
    }


def theme_attributes(theme):
    """Return ``[(tag, attrs)]`` for ``<mj-attributes>`` theme defaults."""
    palette = _palette(theme)
    all_attrs = {}
    text_attrs = {}
    button_attrs = {}

    fonts = theme.fonts.first() if theme is not None else None
    if fonts is not None:
        body = fonts.font_families.filter(role="body").first()
        if body is not None:
            all_attrs["font-family"] = body.css_value
        if fonts.base_font_size:
            text_attrs["font-size"] = str(fonts.base_font_size)
        if fonts.line_height:
            text_attrs["line-height"] = str(fonts.line_height)

    if palette.get("base_content"):
        text_attrs["color"] = palette["base_content"]
    if palette.get("primary"):
        button_attrs["background-color"] = palette["primary"]
    if palette.get("primary_content"):
        button_attrs["color"] = palette["primary_content"]

    radii = theme.radii.first() if theme is not None else None
    if radii is not None and radii.field:
        button_attrs["border-radius"] = str(radii.field)

    entries = []
    for tag, attrs in (
        ("mj-all", all_attrs),
        ("mj-text", text_attrs),
        ("mj-button", button_attrs),
    ):
        if attrs:
            entries.append((tag, attrs))
    return entries


def font_urls(theme):
    """Return ``[{name, href}]`` for the theme's email-hosted fonts."""
    if theme is None:
        return []
    fonts = theme.fonts.first()
    if fonts is None:
        return []
    return [
        {"name": family.font_family, "href": family.url}
        for family in fonts.font_families.all()
        if family.url
    ]


def category_classes(design_value, theme):
    """Return ``[(mj_class_name, attrs)]`` for the template's default design."""
    if not design_value:
        return []
    styles = PageDesignBlock().get_default_style(design_value, theme)
    classes = []
    for category, declarations in styles.items():
        tag = CATEGORY_TAGS.get(category)
        if not tag or not declarations:
            continue
        attrs, _leftover = split_style(declarations, ATTR_MAPS.get(tag, {}))
        if attrs:
            classes.append((f"daisie-{category}", attrs))
    return classes


def body_background_color(theme):
    return _palette(theme).get("base_100", "")


def render_mjml(template):
    context = template.get_mjml_context()
    context.setdefault("mjml_styles", {})
    context["mjml_body"] = render_to_string(
        "wagtail_daisIE/emails/blocks/body_body.html", context
    )
    return render_to_string("wagtail_daisIE/emails/blocks/body.html", context)
