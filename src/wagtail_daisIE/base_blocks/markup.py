"""Single-line text with rudimentary inline markup.

Supported (no nesting): ``**bold**``, ``_italic_``, ``__underline__``,
``~~strikethrough~~`` and ``[text](url)``. Input to
:func:`render_inline_markup` is expected to be HTML-escaped already (the
``daisie_markup`` template tag runs ``render_placeholders`` first).
"""

from __future__ import annotations

import re

from django.utils.safestring import mark_safe
from wagtail import blocks


_MARKUP_RE = re.compile(
    r"\*\*(?P<bold>.+?)\*\*"
    r"|~~(?P<strike>.+?)~~"
    r"|__(?P<underline>.+?)__"
    r"|_(?P<italic>.+?)_"
    r"|\[(?P<link_text>[^\]]+)\]\((?P<link_url>[^)]+)\)",
    re.DOTALL,
)


class InlineMarkupBlock(blocks.CharBlock):
    """Single-line text with rudimentary markup."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "help_text",
            "Supports **bold**, _italic_, __underline__, ~~strikethrough~~ "
            "and [links](https://example.com).",
        )
        super().__init__(*args, **kwargs)


def render_inline_markup(value, *, allow_links=True):
    """Render rudimentary markup in an already escaped string to HTML."""
    if value is None:
        return ""
    text = str(value)

    def replace(match):
        if match.group("bold") is not None:
            return f"<strong>{match.group('bold')}</strong>"
        if match.group("strike") is not None:
            return f"<s>{match.group('strike')}</s>"
        if match.group("underline") is not None:
            return f"<u>{match.group('underline')}</u>"
        if match.group("italic") is not None:
            return f"<em>{match.group('italic')}</em>"
        label = match.group("link_text")
        if not allow_links:
            return label
        from ..dynamic.resolvers import sanitize_url

        url = sanitize_url(match.group("link_url"))
        if not url:
            return label
        return f'<a class="link" href="{url}">{label}</a>'

    return mark_safe(_MARKUP_RE.sub(replace, text))  # noqa: S308


def strip_inline_markup(value):
    """Return ``value`` with the markup markers removed (for HTML attributes)."""
    if value is None:
        return ""

    def replace(match):
        if match.group("link_text") is not None:
            return match.group("link_text")
        for name in ("bold", "strike", "underline", "italic"):
            inner = match.group(name)
            if inner is not None:
                return inner
        return match.group(0)

    return _MARKUP_RE.sub(replace, str(value))
