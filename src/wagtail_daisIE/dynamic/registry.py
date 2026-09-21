"""Context-model registry.

Projects declare models that authors may reference in content via
``WAGTAIL_DAISIE_CONTEXT_MODELS``::

    WAGTAIL_DAISIE_CONTEXT_MODELS = {
        "user": {
            "label": _("Current user"),
            "model": "users.User",
            "source": "request.user",
        },
        "meeting": {
            "label": _("Meeting"),
            "model": "meetings.Meeting",
            "source": "url",
            "lookup_field": "slug",
            "url_source": "get_absolute_url",
        },
    }

Resolving a configured model never happens at import time; the dotted model
path is only imported when the model is first needed.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass, field

from django.apps import apps
from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)

SETTING_NAME = "WAGTAIL_DAISIE_CONTEXT_MODELS"

_context_models_cache: dict[str, ContextModel] | None = None


@dataclass
class ContextModel:
    """A single entry from ``WAGTAIL_DAISIE_CONTEXT_MODELS``."""

    key: str
    label: object
    model_path: str
    source: object = "request.user"
    lookup_field: str = "pk"
    url_source: str = ""
    select_related: tuple[str, ...] = ()
    prefetch_related: tuple[str, ...] = ()
    fields: tuple[str, ...] = ()
    queryset_path: object = ""
    filters_config: dict = field(default_factory=dict)
    _resolved_model: object = field(default=None, repr=False)
    _resolved_queryset: object = field(default=None, repr=False)
    _resolved_filters: object = field(default=None, repr=False)

    @property
    def model(self):
        """Return the concrete model class, importing it lazily."""
        if self._resolved_model is None:
            self._resolved_model = resolve_model(self.model_path)
        return self._resolved_model

    def get_filters(self):
        """Return the normalised filter definitions for this model."""
        if self._resolved_filters is None:
            filters = {}
            for key, raw in (self.filters_config or {}).items():
                if not isinstance(raw, dict):
                    continue
                spec = dict(raw)
                spec.setdefault("type", "choice")
                spec.setdefault("label", key.replace("_", " ").title())
                filters[key] = spec
            self._resolved_filters = filters
        return self._resolved_filters

    def get_queryset(self, request=None, page=None):
        """Return the configured base queryset, or ``None`` to use the default.

        The ``queryset`` setting may be a dotted path or a callable, called as
        ``queryset(request, page)`` (falling back to a no-argument call).
        """
        target = self.queryset_path
        if not target:
            return None
        func = self._resolved_queryset
        if func is None:
            if callable(target):
                func = target
            else:
                try:
                    func = import_string(target)
                except ImportError:
                    logger.warning("Could not resolve context queryset %r", target)
                    func = False
            self._resolved_queryset = func
        if not callable(func):
            return None
        try:
            return func(request, page)
        except TypeError:
            return func()

    @property
    def is_callable_source(self):
        return callable(self.source)

    @property
    def source_kind(self):
        return "url" if self.source == "url" else "automatic"

    @property
    def is_automatic(self):
        return self.source_kind == "automatic"

    @property
    def supports_url(self):
        return self.source_kind == "url"

    @property
    def supports_fixed(self):
        return self.model is not None

    @property
    def modes(self):
        if self.supports_url:
            return ["url", "fixed"] if self.supports_fixed else ["url"]
        return ["automatic"]

    @property
    def source_summary(self):
        source = self.source
        if callable(source):
            return _("Resolved automatically by a project function.")
        source = str(source or "")
        if source == "url":
            return _("Looked up from a URL keyword.")
        if source == "page":
            return _("The current page.")
        if source.startswith("request"):
            attribute = source.split(".", 1)[1] if "." in source else ""
            return {
                "user": _("The current user."),
                "site": _("The current site."),
            }.get(attribute, _("From the current request."))
        return _("Resolved automatically.")

    def field_docs(self, limit=20):
        model = self.model
        if model is None:
            return []
        docs = []
        for model_field in list(model._meta.fields)[:limit]:
            label = getattr(model_field, "verbose_name", None) or model_field.name
            docs.append({"name": model_field.name, "label": str(label)})
        return docs

    def examples(self, limit=4):
        items = [f"{{{{ {self.key} }}}}"]
        if self.url_source or self.supports_url:
            items.append(f"{{{{ {self.key}.url }}}}")
        for doc in self.field_docs(limit=limit):
            items.append(f"{{{{ {self.key}.{doc['name']} }}}}")
        return items

    def __str__(self):
        return str(self.label)


def resolve_model(path):
    """Resolve ``"app_label.ModelName"`` or a dotted import path to a model."""
    if not path:
        return None
    try:
        return apps.get_model(path)
    except (LookupError, ValueError):
        pass
    try:
        return import_string(path)
    except ImportError:
        logger.warning("Could not resolve context model %r", path)
        return None


def _as_tuple(value):
    if not value:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(value)


def _build_context_model(key, raw, **overrides):
    raw = dict(raw or {})
    raw.update(overrides)
    return ContextModel(
        key=key,
        label=raw.get("label") or key.replace("_", " ").title(),
        model_path=raw.get("model", ""),
        source=raw.get("source", "request.user"),
        lookup_field=raw.get("lookup_field", "pk") or "pk",
        url_source=raw.get("url_source", "") or "",
        select_related=_as_tuple(raw.get("select_related")),
        prefetch_related=_as_tuple(raw.get("prefetch_related")),
        fields=_as_tuple(raw.get("fields")),
        queryset_path=raw.get("queryset", "") or "",
        filters_config=dict(raw.get("filters") or {}),
    )


def get_context_models(*, use_cache=True):
    """Return the configured context models keyed by their context variable."""
    global _context_models_cache
    if use_cache and _context_models_cache is not None:
        return _context_models_cache

    raw_config = getattr(settings, SETTING_NAME, {}) or {}
    models = {}
    for key, raw in raw_config.items():
        if not isinstance(raw, dict):
            continue
        try:
            models[key] = _build_context_model(key, raw)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Invalid context model config for %r", key)
    _context_models_cache = models
    return models


def reset_context_models():
    """Clear the cached registry (used by tests and ``override_settings``)."""
    global _context_models_cache
    _context_models_cache = None


def get_context_model(key):
    return get_context_models().get(key)


def get_context_model_keys():
    return list(get_context_models().keys())


def get_context_model_choices():
    """Choices callable for admin blocks/panels (lazy, never queries)."""
    return [(key, config.label) for key, config in get_context_models().items()]


def get_filter_choices():
    """Choices for selecting a configured filter (namespaced by model key)."""
    choices = []
    for model_key, config in get_context_models().items():
        for filter_key, spec in config.get_filters().items():
            label = f"{config.label}: {spec.get('label', filter_key)}"
            choices.append((f"{model_key}:{filter_key}", label))
    return choices


def get_context_models_state():
    """Return JSON-safe binding metadata for the admin JS adapter."""
    state = {}
    for key, config in get_context_models().items():
        model = config.model
        state[key] = {
            "label": str(config.label),
            "model": model._meta.label if model else config.model_path,
            "modelPath": config.model_path,
            "automatic": config.is_automatic,
            "modes": config.modes,
            "sourceSummary": str(config.source_summary),
            "lookupField": config.lookup_field,
            "urlSource": config.url_source,
            "fields": config.field_docs(),
            "examples": config.examples(),
        }
    return state
