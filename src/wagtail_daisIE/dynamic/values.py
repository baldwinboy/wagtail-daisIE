"""Normalisation helpers for dynamic values.

Placeholders, template filters and data blocks all need the same empty-value
semantics: ``None``, empty managers, empty querysets and empty sequences render
as an empty string rather than a model-manager representation.
"""

from __future__ import annotations

from django.db.models import Manager, QuerySet
from django.utils.safestring import SafeData


def iter_values(value):
    """Return a list for managers, querysets and sequence values.

    Managers and querysets are materialised through ``.all()``. Arbitrary
    callables are not invoked.
    """
    if value is None:
        return []
    if isinstance(value, (Manager, QuerySet)) or callable(getattr(value, "all", None)):
        return list(value.all())
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=str)
    return [value]


def normalize_text_value(value):
    """Return a readable, consistently empty-aware string.

    ``None`` and empty managers/querysets/sequences become ``""``. Non-empty
    managers and querysets are joined into a readable comma-separated value.
    Safe strings are returned unchanged so ``|safe`` behaviour is preserved.
    """
    if value is None:
        return ""
    if isinstance(value, SafeData):
        return value
    values = iter_values(value)
    if not values:
        return ""
    if len(values) == 1 and not isinstance(
        value, (Manager, QuerySet, list, tuple, set, frozenset)
    ):
        return str(values[0])
    return ", ".join(str(item) for item in values)


__all__ = ["iter_values", "normalize_text_value"]
