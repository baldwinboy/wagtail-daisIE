"""Mixins that inject configured context models into page rendering."""

from __future__ import annotations

from .resolvers import resolve_context_models


class DaisieContextMixin:
    """Resolve ``WAGTAIL_DAISIE_CONTEXT_MODELS`` into the page context.

    The mixin is deliberately independent of Wagtail's ``Page``: any view or
    model with ``context_bindings`` can use it.
    """

    def get_daisie_context(self, request, page=None):
        return resolve_context_models(request, page if page is not None else self)

    def add_daisie_context(self, request, context):
        for key, value in self.get_daisie_context(request).items():
            context.setdefault(key, value)
        return context
