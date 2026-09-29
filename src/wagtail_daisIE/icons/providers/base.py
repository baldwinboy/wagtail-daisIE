"""Icon provider base class and helpers."""

import re

from django.utils.html import escape


_SVG_OPEN = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)
_ATTRS = {
    "width": re.compile(r'\s+width="[^"]*"', re.IGNORECASE),
    "height": re.compile(r'\s+height="[^"]*"', re.IGNORECASE),
    "fill": re.compile(r"\s+fill=\"[^\"]*\"", re.IGNORECASE),
    "stroke": re.compile(r"\s+stroke=\"[^\"]*\"", re.IGNORECASE),
}


def style_value(size=None, color=None):
    """Build the raw inline style value for an icon's size and colour."""
    styles = []
    if size:
        styles.append(f"font-size: {size}")
    if color:
        styles.append(f"color: {color}")
    return "; ".join(styles)


def style_attrs(size=None, color=None):
    """Build an inline ``style`` string for an icon's size and colour."""
    value = style_value(size, color)
    return f' style="{value}"' if value else ""


def normalize_icon_svg(html, size=None, color=None):
    """Make an inline SVG scale and colour with its parent element.

    The root ``<svg>`` is given ``width``/``height`` in ``em`` (so it follows a
    button's ``font-size``) and an inherited ``currentColor`` colour (so it
    follows the button's text colour). Explicit ``size``/``color`` override
    those defaults.
    """
    if not html or "<svg" not in html:
        return html
    dimension = escape(str(size or "1em"))
    color_value = escape(str(color or "currentColor"))

    def _replace(match):
        tag = _ATTRS["width"].sub("", match.group(0))
        tag = _ATTRS["height"].sub("", tag)
        tag = tag[:-1].rstrip() + f' width="{dimension}" height="{dimension}"'
        if not _ATTRS["fill"].search(tag) and not _ATTRS["stroke"].search(tag):
            tag += f' fill="{color_value}"'
        return tag + ">"

    return _SVG_OPEN.sub(_replace, html, count=1)


class IconProvider:
    """Base class for an icon source.

    Subclasses implement ``render`` and, when searchable/browsable,
    ``search``/``browse``. Providers must never query the database at import
    time or in ``__init__``.
    """

    kind = "custom"
    search_enabled = True
    enabled = True

    def __init__(self, prefix, label, **options):
        self.prefix = prefix
        self.label = label
        self.options = options

    def head_assets(self):
        """Return a list of ``{"type": "script"|"css", "url": ...}`` assets."""
        return []

    def render(self, name, size=None, color=None):
        """Return safe HTML for a single icon (without accessibility wrapper)."""
        raise NotImplementedError

    def email_svg(self, name, color=None):
        """Return a raw inline SVG for email rendering (no size/colour attrs).

        Providers that cannot produce inline SVG (webfonts, web components)
        return an empty string.
        """
        return ""

    def choice_label(self, name):
        return name

    def search(self, query, limit=64, start=0):
        """Return a list of ``{"value", "name", "label"}`` dicts."""
        return []

    def browse(self, limit=None):
        """Return icons available without a search query."""
        return []

    def info(self):
        """Return provider metadata (name, licence, total, ...)."""
        return {}

    def __repr__(self):
        return f"<{type(self).__name__} prefix={self.prefix!r}>"
