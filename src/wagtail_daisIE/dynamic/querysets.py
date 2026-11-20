"""Shared queryset helpers for context models.

Centralising these paths keeps feed queries and binding search consistent in
their filtering, eager loading and safe search behaviour.
"""

from __future__ import annotations

import inspect
import logging

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q


logger = logging.getLogger(__name__)

SAFE_SEARCH_FIELDS = ("title", "name", "slug", "label")
UNSAFE_SEARCH_FIELD_PARTS = ("password", "secret", "token", "hash", "api_key")


def call_with_request_page(func, request=None, page=None):
    """Call ``func`` with the arguments its signature accepts."""
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        # Fall back to the two-argument form for callables whose signature
        # cannot be inspected (builtins and some partials).
        return func(request, page)

    parameters = signature.parameters
    positional = [
        parameter
        for parameter in parameters.values()
        if parameter.kind
        in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    ]
    variadic = any(
        parameter.kind == parameter.VAR_POSITIONAL for parameter in parameters.values()
    )

    if variadic or len(positional) >= 2:
        return func(request, page)
    if len(positional) == 1:
        return func(request)
    return func()


def base_queryset(config, request=None, page=None):
    """Return the configured base queryset for ``config``, or ``None``."""
    if config is None or getattr(config, "model", None) is None:
        return None
    queryset = config.get_queryset(request, page)
    if queryset is None:
        queryset = config.model._default_manager.all()
    if getattr(config, "select_related", ()):
        queryset = queryset.select_related(*config.select_related)
    if getattr(config, "prefetch_related", ()):
        queryset = queryset.prefetch_related(*config.prefetch_related)
    return queryset


def _is_password_like(name):
    lowered = name.lower()
    return any(part in lowered for part in UNSAFE_SEARCH_FIELD_PARTS)


def search_field_names(config):
    """Return the safe, model-present search field names for ``config``."""
    model = getattr(config, "model", None)
    if model is None:
        return ()

    explicit = getattr(config, "search_fields", ()) or ()
    if explicit:
        names = tuple(explicit)
    else:
        present = {field.name for field in model._meta.fields}
        names = tuple(name for name in SAFE_SEARCH_FIELDS if name in present)

    safe = []
    for name in names:
        path = name.split("__", 1)[0]
        try:
            model._meta.get_field(path)
        except FieldDoesNotExist:
            logger.warning(
                "Context model %r declares unknown search field %r; ignoring it.",
                getattr(config, "key", None),
                name,
            )
            continue
        if _is_password_like(name):
            logger.warning(
                "Context model %r search field %r is password-like; ignoring it.",
                getattr(config, "key", None),
                name,
            )
            continue
        safe.append(name)
    return tuple(safe)


def search_queryset(queryset, config, query, limit=50):
    """Filter and bound ``queryset`` using the configured search fields."""
    if queryset is None:
        return None
    limit = max(1, int(limit or 50))
    query = (query or "").strip()
    if not query:
        return queryset[:limit]

    fields = search_field_names(config)
    if not fields:
        logger.warning(
            "Context model %r has no searchable fields; returning no results.",
            getattr(config, "key", None),
        )
        return queryset.none()[:limit]

    condition = Q()
    for field_name in fields:
        condition |= Q(**{f"{field_name}__icontains": query})
    return queryset.filter(condition)[:limit]


__all__ = [
    "UNSAFE_SEARCH_FIELD_PARTS",
    "SAFE_SEARCH_FIELDS",
    "base_queryset",
    "call_with_request_page",
    "search_field_names",
    "search_queryset",
]
