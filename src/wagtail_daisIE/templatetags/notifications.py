"""Template tags that inject placeholders into rendered content.

Usage in templates::

    {% load notifications %}
    <p>{% daisie_text value.text %}</p>
    <div>{% daisie_richtext value.text %}</div>
    <mj-raw>{% daisie_html value.html %}</mj-raw>

``daisie_text`` escapes literal text (for plain/char fields), ``daisie_html``
preserves it (for raw HTML) and ``daisie_richtext`` additionally expands and
sanitises Wagtail rich text.
"""

from __future__ import annotations

import re

from html import unescape

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from wagtail.templatetags.wagtailcore_tags import richtext as _richtext

from ..base_blocks.markup import render_inline_markup, strip_inline_markup
from ..notifications.context import context_from_template_context
from ..notifications.placeholders import render_expression, render_placeholders


register = template.Library()


#: Matches an ``<a>`` tag carrying a context-bound (dynamic) link marker.
_DYNAMIC_ANCHOR_RE = re.compile(
    r'<a\b(?=[^>]*\bdata-dynamic="(?P<expr>[^"]*)")[^>]*>',
    re.IGNORECASE,
)


def resolve_dynamic_links(html, data):
    """Resolve ``data-dynamic`` anchors produced by the styled-link handler.

    The database holds ``<a href="#" data-dynamic="{expr}">`` because link
    handlers have no request/context. By the time rich text is rendered here we
    do, so each expression is resolved with :func:`resolve_dynamic_url` (which
    sanitises the scheme) and written back as ``href``.
    """
    from ..dynamic.resolvers import resolve_dynamic_url

    def _replace(match):
        tag = match.group(0)
        expression = unescape(match.group("expr"))
        url = resolve_dynamic_url(expression, data)
        tag = re.sub(r'\s+href="[^"]*"', "", tag, count=1)
        tag = re.sub(r'\s+data-dynamic="[^"]*"', "", tag, count=1)
        tag = re.sub(r'\s+linktype="dynamic"', "", tag, count=1)
        if url:
            tag = tag[:-1] + f' href="{escape(url)}">'
        return tag

    return _DYNAMIC_ANCHOR_RE.sub(_replace, html)


@register.simple_tag(takes_context=True)
def daisie_text(context, value):
    """Substitute placeholders in a plain text field, escaping literals."""
    data = context_from_template_context(context)
    return mark_safe(render_placeholders(value, data, escape_literals=True))  # noqa: S308


@register.simple_tag(takes_context=True)
def daisie_html(context, value):
    """Substitute placeholders while preserving author-written HTML."""
    data = context_from_template_context(context)
    return mark_safe(render_placeholders(value, data, escape_literals=False))  # noqa: S308


@register.simple_tag(takes_context=True)
def daisie_richtext(context, value):
    """Substitute placeholders in rich text, then expand and sanitise it.

    Context-bound (dynamic) links are resolved *first*, on the raw stored HTML,
    so the ``{{ … }}`` inside a ``data-dynamic`` attribute is not consumed by
    the generic placeholder pass before it can be resolved with URL validation.
    """
    data = context_from_template_context(context)
    resolved = resolve_dynamic_links(str(value), data)
    substituted = render_placeholders(resolved, data, escape_literals=False)
    return _richtext(substituted)


@register.simple_tag(takes_context=True)
def daisie_expr(context, expression):
    """Resolve a single expression such as ``bread.pk`` against the context."""
    data = context_from_template_context(context)
    return render_expression(expression, data)


@register.simple_tag(takes_context=True)
def daisie_markup(context, value, allow_links=True):
    """Substitute placeholders then render rudimentary inline markup."""
    data = context_from_template_context(context)
    return render_inline_markup(
        render_placeholders(value, data, escape_literals=True),
        allow_links=allow_links,
    )


@register.filter
def daisie_strip_markup(value):
    """Strip markup markers for use in HTML attributes."""
    return strip_inline_markup(value)
