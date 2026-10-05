"""Form field-type registry.

Projects extend the field types available to form pages in settings::

    WAGTAIL_DAISIE_FORM_FIELD_TYPES = {
        "file": {
            "label": _("File upload"),
            "field": "django.forms.FileField",
            "widget": "django.forms.ClearableFileInput",
            "css": "file-input w-full",
            "is_upload": True,
            "handler": "myapp.uploads.store",
        },
    }

``field`` may be a Django form field class or a factory taking
``(form_field, options)`` and returning a bound field (for example a
``MultipleFileField``). Every dotted path is imported lazily; nothing here
touches the database or resolves components at import time.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass, field

from django.utils.module_loading import import_string

from .conf import get_default_upload_handler_path, get_field_type_config


logger = logging.getLogger(__name__)

#: ``field_type`` is a ``CharField`` of this length on ``DaisieFormField``.
FIELD_TYPE_MAX_LENGTH = 16

_MISSING = object()

_form_field_types_cache: dict[str, FormFieldType] | None = None


@dataclass
class FormFieldType:
    """A single entry from ``WAGTAIL_DAISIE_FORM_FIELD_TYPES``."""

    key: str
    label: object
    field_path: object = ""
    widget_path: object = ""
    widget_attrs: dict = field(default_factory=dict)
    css: str = ""
    options: dict = field(default_factory=dict)
    is_upload: bool = False
    handler_path: object = ""
    _resolved_field: object = field(default=_MISSING, repr=False)
    _resolved_widget: object = field(default=_MISSING, repr=False)
    _resolved_handler: object = field(default=_MISSING, repr=False)

    def __str__(self):
        return str(self.label or self.key)

    @property
    def field(self):
        """Return the form field class/factory, importing it lazily."""
        if self._resolved_field is _MISSING:
            self._resolved_field = _resolve(self.field_path)
        return self._resolved_field

    @property
    def widget(self):
        """Return the widget class/instance, importing it lazily."""
        if self._resolved_widget is _MISSING:
            self._resolved_widget = _resolve(self.widget_path)
        return self._resolved_widget

    @property
    def handler(self):
        """Return the upload handler callable, importing it lazily."""
        if self._resolved_handler is _MISSING:
            self._resolved_handler = _resolve(self.handler_path)
        return self._resolved_handler


def _resolve(target):
    """Resolve a dotted path or callable to a component, or ``None``."""
    if not target:
        return None
    if callable(target):
        return target
    try:
        return import_string(target)
    except ImportError:
        logger.warning("Could not resolve form field component %r", target)
        return None


def _build_field_type(key, raw):
    raw = dict(raw or {})
    if len(key) > FIELD_TYPE_MAX_LENGTH:
        logger.warning(
            "Form field type %r is longer than %d characters and cannot be "
            "stored on DaisieFormField.field_type.",
            key,
            FIELD_TYPE_MAX_LENGTH,
        )
    return FormFieldType(
        key=key,
        label=raw.get("label") or key.replace("_", " ").title(),
        field_path=raw.get("field", "") or "",
        widget_path=raw.get("widget", "") or "",
        widget_attrs=dict(raw.get("widget_attrs") or {}),
        css=raw.get("css", "") or "",
        options=dict(raw.get("options") or {}),
        is_upload=bool(raw.get("is_upload", False)),
        handler_path=raw.get("handler", "") or "",
    )


def get_form_field_types(*, use_cache=True):
    """Return the configured field types keyed by their ``field_type`` value."""
    global _form_field_types_cache
    if use_cache and _form_field_types_cache is not None:
        return _form_field_types_cache

    types = {}
    for key, raw in get_field_type_config().items():
        if not isinstance(raw, dict):
            continue
        try:
            types[key] = _build_field_type(key, raw)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Invalid form field type config for %r", key)
    _form_field_types_cache = types
    return types


def reset_form_field_types():
    """Clear the cached registry (used by tests and ``override_settings``)."""
    global _form_field_types_cache
    _form_field_types_cache = None


def get_form_field_type(key):
    """Return a single configured field type, or ``None``."""
    return get_form_field_types().get(key)


def is_upload_field_type(key):
    """Return whether the field type accepts an uploaded file."""
    spec = get_form_field_type(key)
    return bool(spec is not None and spec.is_upload)


def get_default_upload_handler():
    """Return the project-wide upload handler callable, or ``None``."""
    return _resolve(get_default_upload_handler_path())


def get_form_field_type_choices():
    """Choices callable for the field type select (lazy, never queries)."""
    from wagtail.contrib.forms.models import FORM_FIELD_CHOICES

    choices = dict(FORM_FIELD_CHOICES)
    for key, spec in get_form_field_types().items():
        choices[key] = spec.label
    return list(choices.items())


__all__ = [
    "FIELD_TYPE_MAX_LENGTH",
    "FormFieldType",
    "get_default_upload_handler",
    "get_form_field_type",
    "get_form_field_type_choices",
    "get_form_field_types",
    "is_upload_field_type",
    "reset_form_field_types",
]
