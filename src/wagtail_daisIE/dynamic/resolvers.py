"""Resolve configured context models and dynamic value expressions.

Everything here runs lazily at render time and never at import.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass
from urllib.parse import urlsplit

from django.db.models import Q
from django.utils.module_loading import import_string

from .registry import (
    ContextModel,
    get_context_model,
    get_context_models,
)


logger = logging.getLogger(__name__)

#: URL schemes allowed in dynamic link destinations.
ALLOWED_URL_SCHEMES = frozenset({"", "http", "https", "mailto", "tel"})


@dataclass
class ContextBinding:
    """A per-page (or per-menu) override for a context-model variable."""

    key: str
    mode: str = "automatic"
    object_id: int | None = None
    lookup_field: str = ""
    fallback: str = ""


def resolve_url_kwargs(request):
    """Return the URL kwargs of the matched view (or an empty dict)."""
    match = getattr(request, "resolver_match", None)
    kwargs = getattr(match, "kwargs", None)
    return dict(kwargs or {})


def _lookup(value, attr):
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get(attr)
    if attr.isdigit() and isinstance(value, (list, tuple)):
        try:
            return value[int(attr)]
        except IndexError:
            return None
    return getattr(value, attr, None)


def resolve_object(expression, context):
    """Resolve a dotted expression such as ``user.profile.image`` to an object.

    Braces and simple filters are stripped; only dotted attribute/index lookups
    are supported.
    """
    expression = (expression or "").strip()
    if expression.startswith("{{") and expression.endswith("}}"):
        expression = expression[2:-2].strip()
    expression = expression.split("|", 1)[0].strip()
    if not expression:
        return None
    parts = expression.split(".")
    root = parts[0]
    if root not in context:
        return None
    value = context[root]
    for attr in parts[1:]:
        value = _lookup(value, attr)
        if value is None:
            return None
    return value


def sanitize_url(value):
    """Return ``value`` if it uses an allowed scheme, else an empty string."""
    if value is None:
        return ""
    url = str(value).strip()
    if not url:
        return ""
    scheme = urlsplit(url).scheme.lower()
    if scheme not in ALLOWED_URL_SCHEMES:
        return ""
    return url


def context_model_for_instance(instance):
    """Return the registry entry whose model matches ``instance``."""
    if instance is None:
        return None
    model = instance if isinstance(instance, type) else type(instance)
    for config in get_context_models().values():
        candidate = config.model
        if candidate is None:
            continue
        if issubclass(model, candidate):
            return config
    return None


def url_for_object(obj, config=None):
    """Derive a (sanitised) URL from a model instance or string."""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return sanitize_url(obj)

    if config is None:
        config = context_model_for_instance(obj)

    url_source = getattr(config, "url_source", "") if config else ""
    if url_source:
        if url_source == "get_absolute_url":
            getter = getattr(obj, "get_absolute_url", None)
            if callable(getter):
                try:
                    return sanitize_url(getter())
                except Exception:
                    logger.debug("get_absolute_url failed for %r", obj)
        elif hasattr(obj, url_source):
            return sanitize_url(getattr(obj, url_source))
        else:
            try:
                resolver = import_string(url_source)
            except ImportError:
                resolver = None
            if callable(resolver):
                try:
                    return sanitize_url(resolver(obj))
                except Exception:
                    logger.debug("url_source callable failed for %r", obj)

    getter = getattr(obj, "get_absolute_url", None)
    if callable(getter):
        try:
            return sanitize_url(getter())
        except Exception:
            logger.debug("get_absolute_url failed for %r", obj)
    return sanitize_url(getattr(obj, "url", ""))


def resolve_dynamic_url(expression, context):
    """Resolve a dynamic link expression to a sanitised URL."""
    expression = (expression or "").strip()
    if not expression:
        return ""
    root = expression.split("|", 1)[0].replace("{{", "").replace("}}", "").strip()
    root = root.split(".")[0].strip()
    config = get_context_model(root) if root else None

    value = resolve_object(expression, context)
    if isinstance(value, str):
        return sanitize_url(value)
    if value is not None:
        return url_for_object(value, config)
    # ``{{ meeting.url }}`` where the model has no ``url`` attribute: fall back
    # to the configured url_source on the root object.
    if config is not None:
        return url_for_object(context.get(root), config)
    return ""


# --- Context binding parsing / resolution ----------------------------------


def _mapping_value(value):
    if hasattr(value, "value"):
        value = value.value
    return value if isinstance(value, dict) else {}


def _binding_from_value(value):
    raw = _mapping_value(value)
    object_id = raw.get("object_id")
    try:
        object_id = int(object_id) if object_id not in (None, "") else None
    except (TypeError, ValueError):
        object_id = None
    return ContextBinding(
        key=str(raw.get("key", "") or ""),
        mode=str(raw.get("mode", "automatic") or "automatic"),
        object_id=object_id,
        lookup_field=str(raw.get("lookup_field", "") or ""),
        fallback=str(raw.get("fallback", "") or ""),
    )


def parse_bindings(page):
    """Return ``{key: ContextBinding}`` from a page's ``context_bindings``."""
    bindings = {}
    stream = getattr(page, "context_bindings", None)
    if not stream:
        return bindings
    try:
        children = list(stream)
    except TypeError:
        return bindings
    for child in children:
        raw = _mapping_value(child)
        binding = _binding_from_value(raw)
        if binding.key:
            bindings[binding.key] = binding
    return bindings


def _base_queryset(model, config):
    if model is None:
        return None
    qs = model._default_manager.all()
    if config is not None and config.select_related:
        qs = qs.select_related(*config.select_related)
    if config is not None and config.prefetch_related:
        qs = qs.prefetch_related(*config.prefetch_related)
    return qs


def _resolve_fixed(config, binding):
    model = config.model
    if model is None or binding is None or not binding.object_id:
        return None
    queryset = _base_queryset(model, config)
    if queryset is None:
        return None
    return queryset.filter(pk=binding.object_id).first()


def _resolve_url(config, binding, request):
    model = config.model
    lookup_field = (
        binding.lookup_field
        if binding is not None and binding.lookup_field
        else config.lookup_field
    ) or "pk"
    kwargs = resolve_url_kwargs(request)
    value = kwargs.get(lookup_field) or kwargs.get("pk") or kwargs.get("slug")
    if value is None:
        return None
    queryset = _base_queryset(model, config)
    if queryset is None:
        return None
    return queryset.filter(**{lookup_field: value}).first()


def _resolve_source(config, request, page):
    source = config.source
    if source == "page":
        return page
    if callable(source):
        return source(request, page)
    if isinstance(source, str):
        if source.startswith("request"):
            parts = source.split(".")
            if parts and parts[0] == "request":
                parts = parts[1:]
            obj = request
            for part in parts:
                obj = _lookup(obj, part)
                if obj is None:
                    return None
            return obj
        try:
            resolver = import_string(source)
        except ImportError:
            logger.warning("Could not resolve context source %r", source)
            return None
        return resolver(request, page)
    return None


def _is_missing(value):
    return value is None or value == ""


def _unauthenticated(value):
    return hasattr(value, "is_authenticated") and not value.is_authenticated


def resolve_binding(config: ContextModel, binding, request, page=None):
    """Resolve a single context variable using its config and binding."""
    mode = (binding.mode if binding is not None else "") or config.source_kind

    if mode == "fixed":
        result = _resolve_fixed(config, binding)
    elif mode == "url" or config.source == "url":
        result = _resolve_url(config, binding, request)
    else:
        result = _resolve_source(config, request, page)

    if _is_missing(result) or _unauthenticated(result):
        fallback = binding.fallback if binding is not None else ""
        if fallback:
            return fallback
    return result


def resolve_context_models(request, page=None, bindings=None):
    """Return ``{key: instance_or_fallback}`` for every configured context model."""
    if bindings is None:
        bindings = parse_bindings(page)
    data = {}
    for key, config in get_context_models().items():
        try:
            data[key] = resolve_binding(config, bindings.get(key), request, page)
        except Exception:
            logger.exception("Failed to resolve context model %r", key)
            data[key] = None
    return data


# --- Widget option endpoint -------------------------------------------------


def model_options(model, *, query="", limit=50):
    """Return ``[{id, text}]`` for ``model`` (used by the chooser widget)."""
    if model is None:
        return []
    qs = model._default_manager.all()
    if query:
        condition = Q()
        for field in model._meta.fields:
            if field.get_internal_type() in (
                "CharField",
                "TextField",
                "SlugField",
                "EmailField",
            ):
                condition |= Q(**{f"{field.name}__icontains": query})
        if condition:
            qs = qs.filter(condition)
    options = []
    for obj in qs[:limit]:
        options.append({"id": obj.pk, "text": str(obj)})
    return options
