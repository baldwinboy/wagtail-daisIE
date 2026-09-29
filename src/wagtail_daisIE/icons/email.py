"""Email-safe icon rendering.

Email clients strip inline SVG and cannot evaluate ``currentColor`` or ``em``
sizes, so icons are rendered as a data-URI ``<img>`` with explicit pixel
dimensions and a resolved colour. Only SVG providers can be used; webfont and
web-component providers return an empty string.
"""

from __future__ import annotations

import base64
import re

from django.utils.html import format_html

from .registry import get_provider
from .value import split_icon


_SVG_OPEN = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)
_WIDTH = re.compile(r'\s+width="[^"]*"', re.IGNORECASE)
_HEIGHT = re.compile(r'\s+height="[^"]*"', re.IGNORECASE)
_FILL = re.compile(r'\s+fill="[^"]*"', re.IGNORECASE)
_STROKE = re.compile(r'\s+stroke="[^"]*"', re.IGNORECASE)


def _rewrite_svg(svg, size_px, color):
    """Force explicit pixel dimensions and a literal colour on the root SVG."""

    def _replace(match):
        tag = _WIDTH.sub("", match.group(0))
        tag = _HEIGHT.sub("", tag)
        tag = tag[:-1].rstrip() + f' width="{size_px}" height="{size_px}"'
        if not _FILL.search(tag) and not _STROKE.search(tag):
            tag += f' fill="{color}"'
        return tag + ">"

    return _SVG_OPEN.sub(_replace, svg, count=1)


def render_icon_email(value, *, size_px=16, color="#000000"):
    """Return an ``<img>`` tag for an icon, safe for MJML/email clients."""
    prefix, name = split_icon(value)
    if not name or prefix is None:
        return ""
    provider = get_provider(prefix)
    if provider is None:
        return ""
    svg = provider.email_svg(name, color=color)
    if not svg or "<svg" not in svg:
        return ""
    svg = _rewrite_svg(svg, size_px, color)
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return format_html(
        '<img src="data:image/svg+xml;base64,{}" '
        'width="{}" height="{}" alt="" '
        'style="display:inline-block;vertical-align:-0.125em;" />',
        data,
        size_px,
        size_px,
    )
