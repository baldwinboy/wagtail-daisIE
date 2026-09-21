"""Placeholder substitution for author-written content and email templates.

Authors write Django-style variable expressions, e.g. ``{{ now|date:"j F Y" }}``
or ``{{ payload.meeting_title }}``. At render time the expression is evaluated
with the placeholder context (see :mod:`.context`) so the output contains real
values rather than the literal token.

Only ``{{ ... }}`` expressions are supported. Django template *tags*
(``{% ... %}``) and comments (``{# ... #}``) are deliberately not executed: they
are treated as literal text and reported by :func:`validate_text`.
"""

from __future__ import annotations

import logging
import re

from django.template import Context, Template
from django.utils.html import escape


logger = logging.getLogger(__name__)


#: Matches a single ``{{ expression }}`` token, non-greedily.
TOKEN_RE = re.compile(r"{{\s*(?P<expr>.+?)\s*}}", re.DOTALL)

# Private-use sentinels stand in for syntax we do not want Django to parse.
# Tags/comments are neutralised for the whole string; stray braces are only
# neutralised inside literal segments (the matched ``{{ ... }}`` tokens are
# rebuilt deliberately).
_TAG_SENTINELS = {
    "{%": "\ue000",
    "%}": "\ue001",
    "{#": "\ue002",
    "#}": "\ue003",
}
_BRACE_SENTINELS = {
    "{{": "\ue004",
    "}}": "\ue005",
}
_RESTORE = {value: key for key, value in {**_TAG_SENTINELS, **_BRACE_SENTINELS}.items()}

_TEMPLATE_CACHE: dict[str, Template] = {}
_TEMPLATE_CACHE_LIMIT = 512


def _replace(text, mapping):
    for source, sentinel in mapping.items():
        if source in text:
            text = text.replace(source, sentinel)
    return text


def _neutralize(text):
    return _replace(text, _TAG_SENTINELS)


def _restore(text):
    for sentinel, source in _RESTORE.items():
        if sentinel in text:
            text = text.replace(sentinel, source)
    return text


def _compile(source):
    template = _TEMPLATE_CACHE.get(source)
    if template is None:
        template = Template(source)
        if len(_TEMPLATE_CACHE) >= _TEMPLATE_CACHE_LIMIT:
            _TEMPLATE_CACHE.clear()
        _TEMPLATE_CACHE[source] = template
    return template


def render_placeholders(text, context, *, escape_literals=True, escape_values=True):
    """Substitute ``{{ ... }}`` tokens in ``text`` using ``context``.

    Parameters
    ----------
    text:
        The author-written string. ``None`` renders as an empty string.
    context:
        Mapping used to resolve expressions (``payload``, ``site``, ``now``,
        ``recipient`` ...).
    escape_literals:
        When true (plain text fields) the surrounding literal text is
        HTML-escaped. When false (rich text / raw HTML, which is sanitised
        elsewhere) it is preserved verbatim.
    escape_values:
        Whether substituted values are HTML-escaped. Always true except when
        producing a plain-text representation (e.g. an email subject header).
    """
    if text is None:
        return ""
    text = str(text)
    if "{{" not in text:
        return escape(text) if escape_literals else text

    neutralised = _neutralize(text)
    parts = TOKEN_RE.split(neutralised)
    pieces = []
    for index, part in enumerate(parts):
        if index % 2 == 0:
            part = _replace(part, _BRACE_SENTINELS)
            pieces.append(escape(part) if escape_literals else part)
        else:
            pieces.append("{{ " + part + " }}")

    rendered = _compile("".join(pieces)).render(
        Context(context, autoescape=escape_values)
    )
    return _restore(rendered)


def render_expression(expression, context):
    """Evaluate a single expression such as ``payload.title`` to a string."""
    if expression is None:
        return ""
    expression = str(expression).strip()
    if not expression:
        return ""
    return _compile("{{ " + expression + " }}").render(
        Context(context, autoescape=True)
    )


def extract_variables(text):
    """Return the distinct root variable names referenced in ``text``."""
    found: list[str] = []
    for match in TOKEN_RE.finditer(str(text or "")):
        expression = match.group("expr").strip()
        root = re.split(r"[|.\[(]", expression, maxsplit=1)[0].strip()
        if root and root not in found:
            found.append(root)
    return found


def validate_text(text):
    """Return warnings for unsupported syntax in ``text``."""
    warnings = []
    source = str(text or "")
    if "{%" in source:
        warnings.append(
            "Django template tags ({%% ... %%}) are not supported and will be "
            "shown literally. Use {{ ... }} expressions instead."
        )
    if "{#" in source:
        warnings.append(
            "Django template comments ({# ... #}) are not supported and will "
            "be shown literally."
        )
    return warnings


# --- Help-panel data --------------------------------------------------------

_PLACEHOLDER_PROVIDERS: list = []


def register_placeholder_provider(provider):
    """Register a callable returning extra placeholder groups for the help panel.

    Providers are called lazily when the admin help panel renders and must
    return a list of ``{"title", "description", "items"}`` mappings, where each
    item is ``{"token", "description"}``. Providers must never raise.
    """
    _PLACEHOLDER_PROVIDERS.append(provider)


def _builtin_group():
    return {
        "title": "Always available",
        "description": (
            "These values are available in every email template and content "
            "field, regardless of the bridge or integration in use."
        ),
        "items": [
            {
                "token": "{{ site.hostname }}",
                "description": "Hostname of the current Wagtail site.",
            },
            {
                "token": "{{ site.site_name }}",
                "description": "Human-readable site name.",
            },
            {
                "token": "{{ site.root_url }}",
                "description": "Base URL of the current site.",
            },
            {
                "token": "{{ now }}",
                "description": "Current date and time (use filters to format).",
            },
            {
                "token": '{{ now|date:"j F Y" }}',
                "description": 'Example: renders "12 November 2026" style dates.',
            },
            {
                "token": "{{ recipient.email }}",
                "description": "Email address the message is addressed to.",
            },
            {
                "token": "{{ recipient.name }}",
                "description": "Recipient display name (falls back to email).",
            },
            {
                "token": "{{ recipient.first_name }}",
                "description": "Recipient first name, when known.",
            },
            {
                "token": "{{ recipient.last_name }}",
                "description": "Recipient last name, when known.",
            },
            {
                "token": "{{ recipient.user.profile.… }}",
                "description": "Reach related user data via recipient.user.",
            },
            {
                "token": "{{ payload.… }}",
                "description": (
                    "Values supplied by the bridge, integration or campaign "
                    "that triggered the message."
                ),
            },
        ],
    }


def get_placeholder_groups():
    """Return all placeholder groups for the admin help panel."""
    groups = [_builtin_group()]
    for provider in list(_PLACEHOLDER_PROVIDERS):
        try:
            result = provider()
        except Exception:
            logger.warning("Placeholder provider %r failed", provider, exc_info=True)
            continue
        if result:
            groups.extend(result)
    return groups
