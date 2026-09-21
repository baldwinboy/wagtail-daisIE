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

from django import template
from django.utils.safestring import mark_safe
from wagtail.templatetags.wagtailcore_tags import richtext as _richtext

from ..notifications.context import context_from_template_context
from ..notifications.placeholders import render_expression, render_placeholders


register = template.Library()


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
    """Substitute placeholders in rich text, then expand and sanitise it."""
    data = context_from_template_context(context)
    substituted = render_placeholders(value, data, escape_literals=False)
    return _richtext(substituted)


@register.simple_tag(takes_context=True)
def daisie_expr(context, expression):
    """Resolve a single expression such as ``bread.pk`` against the context."""
    data = context_from_template_context(context)
    return render_expression(expression, data)
