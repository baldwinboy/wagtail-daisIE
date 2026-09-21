"""Helpers for threading context-model values through page/block rendering."""

from __future__ import annotations

from .registry import get_context_model_keys


#: Built-in variables resolved by :mod:`wagtail_daisIE.notifications.context`.
BUILTIN_CONTEXT_KEYS = ("site", "now", "user", "recipient", "payload")


def context_model_keys():
    """Return every context variable name (configured models + built-ins)."""
    return (*get_context_model_keys(), *BUILTIN_CONTEXT_KEYS)


def copy_context_values(parent_context, context):
    """Copy known context values from ``parent_context`` into ``context``.

    Blocks render with their own context dict, so this is what lets nested
    templates (and the ``{% daisie_text %}`` tags) see ``{{ user.x }}``. The
    current ``request`` (and its CSRF token) are carried too, so forms rendered
    inside blocks work.
    """
    if not parent_context:
        return context
    for key in ("request", "csrf_token", *context_model_keys()):
        if key not in context and key in parent_context:
            context[key] = parent_context[key]
    return context
