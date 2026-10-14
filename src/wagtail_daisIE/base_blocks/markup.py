"""Single-line text with inline markup.

Parsing is delegated to ``markdown-it-py`` (CommonMark, HTML disabled) with the
``attrs`` plugin, then the rendered HTML is sanitised. Supported syntax:

* ``**bold**``, ``_italic_``, ``~~strikethrough~~``
* ``__underline__`` (a project extension; CommonMark has no underline)
* ``[text](url)`` links, optionally ``{target=_blank}``
* inline attributes ``{style="…"}`` / ``{.class}``
* a colour shorthand ``{color=primary}`` or ``{color=#rrggbb}`` — named values
  map to the theme's ``var(--color-<name>)`` custom properties

Input is expected to be HTML-escaped already (the ``daisie_markup`` template tag
runs ``render_placeholders`` first); markdown-it preserves entities, so it is not
escaped twice.
"""

from __future__ import annotations

import re

from functools import lru_cache
from html import unescape

from django.utils.html import escape
from django.utils.safestring import mark_safe
from markdown_it import MarkdownIt
from mdit_py_plugins.attrs import attrs_plugin
from wagtail import blocks


#: Private-use sentinels standing in for underline markers, which markdown-it
#: does not understand. They survive parsing untouched so the wrapped content is
#: still parsed (nested emphasis, entities) and correctly escaped.
_UNDERLINE_OPEN = "\uf000"
_UNDERLINE_CLOSE = "\uf001"
_UNDERLINE_RE = re.compile(r"__(.+?)__", re.DOTALL)

#: ``{color=#rrggbb}`` — the attrs plugin cannot read an unquoted ``#``, so quote
#: hex colour values before parsing.
_COLOUR_HEX_RE = re.compile(r"(color=)(#[0-9a-fA-F]{3,8})(?=[}\s])")

_ATTRIBUTE_RE = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*"([^"]*)"')
_ANCHOR_RE = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.DOTALL | re.IGNORECASE)
_SPAN_RE = re.compile(r"<span\b([^>]*)>", re.IGNORECASE | re.DOTALL)

_TOKEN_RE = re.compile(r"[a-zA-Z0-9_-]+\Z")
_HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\Z")
_VAR_RE = re.compile(r"var\(\s*--[a-zA-Z0-9_-]+\s*\)\Z")
_RGB_RE = re.compile(r"rgba?\(\s*[0-9.,%\s/]+\s*\)\Z")
_HSL_RE = re.compile(r"hsla?\(\s*[0-9.,%\s/deg]+\s*\)\Z")
_NUMERIC_RE = re.compile(r"-?\d+(?:\.\d+)?(?:px|em|rem|%|pt|ch|ex|vh|vw)?\Z")
_KEYWORD_RE = re.compile(r"[a-zA-Z-]+\Z")

#: CSS properties an editor may set inline. Everything else is dropped.
_ALLOWED_STYLE_PROPERTIES = frozenset(
    {
        "color",
        "background-color",
        "text-decoration",
        "text-decoration-color",
        "font-weight",
        "font-style",
        "font-size",
    }
)


@lru_cache(maxsize=1)
def _markdown():
    """Return the shared ``MarkdownIt`` parser instance."""
    md = MarkdownIt("commonmark", {"html": False}).enable("strikethrough")
    md.use(
        attrs_plugin,
        spans=True,
        allowed=["style", "target", "rel", "class", "color"],
    )
    return md


def _valid_css_value(value):
    return bool(
        _HEX_RE.fullmatch(value)
        or _VAR_RE.fullmatch(value)
        or _RGB_RE.fullmatch(value)
        or _HSL_RE.fullmatch(value)
        or _NUMERIC_RE.fullmatch(value)
        or _KEYWORD_RE.fullmatch(value)
    )


def _sanitize_style(value):
    """Return the safe declarations of a CSS ``style`` value."""
    if not value:
        return ""
    declarations = []
    for chunk in value.split(";"):
        prop, sep, raw = chunk.partition(":")
        if not sep:
            continue
        prop = prop.strip().lower()
        raw = raw.strip()
        if prop not in _ALLOWED_STYLE_PROPERTIES:
            continue
        if not _valid_css_value(raw):
            continue
        declarations.append(f"{prop}: {raw}")
    return "; ".join(declarations)


def _sanitize_class(value):
    return " ".join(
        token for token in (value or "").split() if _TOKEN_RE.fullmatch(token)
    )


def _map_colour(value):
    """Map a colour shorthand to a safe CSS value, or ``None``."""
    value = (value or "").strip()
    if _HEX_RE.fullmatch(value):
        return value
    if _TOKEN_RE.fullmatch(value):
        return f"var(--color-{value})"
    return None


def _rewrite_span(match):
    attrs = dict(_ATTRIBUTE_RE.findall(match.group(1)))
    style = _sanitize_style(unescape(attrs.get("style", "")))
    colour = _map_colour(unescape(attrs.get("color", "")))
    if colour:
        style = f"{style}; color: {colour}" if style else f"color: {colour}"
    classes = _sanitize_class(unescape(attrs.get("class", "")))
    parts = []
    if style:
        parts.append(f'style="{escape(style)}"')
    if classes:
        parts.append(f'class="{escape(classes)}"')
    return "<span" + (f" {' '.join(parts)}" if parts else "") + ">"


def _rewrite_anchor(match, allow_links):
    attrs = dict(_ATTRIBUTE_RE.findall(match.group(1)))
    body = match.group(2)
    if not allow_links:
        return body
    from ..dynamic.resolvers import sanitize_url

    url = sanitize_url(unescape(attrs.get("href", "")))
    if not url:
        return body
    style = _sanitize_style(unescape(attrs.get("style", "")))
    classes = _sanitize_class(unescape(attrs.get("class", ""))) or "link"
    parts = [f'href="{escape(url)}"', f'class="{escape(classes)}"']
    if style:
        parts.append(f'style="{escape(style)}"')
    if attrs.get("target") == "_blank":
        parts.append('target="_blank"')
        parts.append('rel="noopener noreferrer"')
    return f"<a {' '.join(parts)}>{body}</a>"


def _normalise_colour_attrs(value):
    return _COLOUR_HEX_RE.sub(r'\1"\2"', value)


def _protect_underline(value):
    return _UNDERLINE_RE.sub(
        lambda match: f"{_UNDERLINE_OPEN}{match.group(1)}{_UNDERLINE_CLOSE}",
        value,
    )


def _restore_underline(value):
    return value.replace(_UNDERLINE_OPEN, "<u>").replace(_UNDERLINE_CLOSE, "</u>")


def render_inline_markup(value, *, allow_links=True):
    """Render rudimentary inline markup to sanitised HTML."""
    if value is None:
        return ""
    source = _normalise_colour_attrs(str(value))
    rendered = _markdown().renderInline(_protect_underline(source))
    rendered = _restore_underline(rendered)
    rendered = _ANCHOR_RE.sub(
        lambda match: _rewrite_anchor(match, allow_links),
        rendered,
    )
    rendered = _SPAN_RE.sub(_rewrite_span, rendered)
    return mark_safe(rendered)  # noqa: S308


def strip_inline_markup(value):
    """Return ``value`` with all markup removed (for HTML attributes)."""
    if value is None:
        return ""
    rendered = render_inline_markup(value, allow_links=False)
    return unescape(re.sub(r"<[^>]+>", "", rendered))


class InlineMarkupBlock(blocks.CharBlock):
    """Single-line text with rudimentary markup."""

    def __init__(self, *args, **kwargs):
        # Build the help text that will appear inside the tooltip.
        tooltip_content = (
            "Supports **bold**, _italic_, __underline__, ~~strikethrough~~, "
            "[links](https://example.com) and {color=…} text. See the DaisyUI "
            "Editor Guide → Markup and placeholders.",
        )

        # 1. Suppress the default help text (it would otherwise appear below the field).
        kwargs.setdefault("help_text", "")

        # 2. Attach the tooltip attributes to the field's wrapper.
        kwargs.setdefault("form_attrs", {})
        kwargs["form_attrs"].update(
            {
                "data-controller": "w-tooltip",
                # The content is plain text here; HTML links will not be clickable.
                "data-w-tooltip-content-value": tooltip_content,
                # Optional: adjust placement (top, bottom, left, right, etc.)
                "data-w-tooltip-placement-value": "top",
            }
        )

        super().__init__(*args, **kwargs)
