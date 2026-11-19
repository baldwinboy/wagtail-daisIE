"""Registry and runner for developer-defined actions.

Projects declare actions in settings::

    WAGTAIL_DAISIE_ACTIONS = {
        "basket.add": {
            "label": "Add to basket",
            "handler": "myapp.actions.add_to_basket",
        },
    }

A handler is called as ``handler(request, data)`` where ``data`` is the POST
data. It may return an ``HttpResponse`` (including a redirect); returning
``None`` redirects back to the referring page.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.http import Http404
from django.utils.module_loading import import_string


logger = logging.getLogger(__name__)

SETTING_NAME = "WAGTAIL_DAISIE_ACTIONS"

#: Keys every action field preset may use.
ACTION_FIELD_COMMON_KEYS = frozenset(
    {"type", "name", "label", "required", "field_layout"}
)

#: Supported preset types and their additional keys.
ACTION_FIELD_TYPES = {
    "input": frozenset(
        {"input_type", "placeholder", "value", "helper_text", "error_text"}
    ),
    "textarea": frozenset({"placeholder", "rows", "helper_text", "error_text"}),
    "select": frozenset({"options", "placeholder", "helper_text", "error_text"}),
    "checkbox": frozenset({"checked", "helper_text"}),
    "toggle": frozenset({"checked", "helper_text"}),
    "radio": frozenset({"options", "group_layout", "option_layout"}),
    "range": frozenset({"minimum", "maximum", "step", "value"}),
    "rating": frozenset({"maximum", "value"}),
    "file": frozenset({"accept", "multiple", "helper_text"}),
    "autocomplete": frozenset(
        {
            "options",
            "options_source",
            "selected",
            "value_field",
            "label_field",
            "placeholder",
            "helper_text",
            "error_text",
        }
    ),
}


def get_action_config():
    return getattr(settings, SETTING_NAME, {}) or {}


def get_action_choices():
    """Choices callable for admin blocks (lazy; never queries)."""
    choices = []
    for key, config in get_action_config().items():
        label = config.get("label", key) if isinstance(config, dict) else key
        choices.append((key, label))
    return choices


def get_action_fields(key):
    """Return configured field presets for ``key`` in declaration order."""
    config = get_action_config().get(key)
    if not isinstance(config, dict):
        return []
    fields = config.get("fields")
    if not isinstance(fields, (list, tuple)):
        return []
    return list(fields)


def validate_action_fields(fields):
    """Return configuration error messages for an action's field presets."""
    if not isinstance(fields, (list, tuple)):
        return ["fields must be a list."]

    errors = []
    seen = set()
    for index, field in enumerate(fields, start=1):
        prefix = f"field {index}"
        if not isinstance(field, dict):
            errors.append(f"{prefix} must be a mapping.")
            continue

        field_type = field.get("type")
        if field_type not in ACTION_FIELD_TYPES:
            errors.append(f"{prefix} has unsupported type {field_type!r}.")
            continue

        name = str(field.get("name") or "").strip()
        if not name:
            errors.append(f"{prefix} needs a name.")
        elif name in seen:
            errors.append(f"{prefix} duplicates field name {name!r}.")
        else:
            seen.add(name)
            if len(name) > 64:
                errors.append(f"{prefix} name must be 64 characters or fewer.")

        if not str(field.get("label") or "").strip():
            errors.append(f"{prefix} needs a label.")
        if "required" in field and not isinstance(field["required"], bool):
            errors.append(f"{prefix} required must be true or false.")

        if field_type in {"select", "radio"} and not field.get("options"):
            errors.append(f"{prefix} needs options.")
        if field_type == "autocomplete" and not (
            field.get("options") or field.get("options_source")
        ):
            errors.append(f"{prefix} needs options or options_source.")

        allowed = ACTION_FIELD_COMMON_KEYS | ACTION_FIELD_TYPES[field_type]
        unknown = sorted(set(field) - allowed)
        if unknown:
            errors.append(f"{prefix} has unsupported keys: {', '.join(unknown)}.")

    return errors


def resolve_action(key):
    """Return the handler callable for ``key``, or ``None``."""
    config = get_action_config().get(key)
    if not config:
        return None
    handler = config.get("handler") if isinstance(config, dict) else config
    if callable(handler):
        return handler
    try:
        return import_string(handler)
    except ImportError:
        logger.warning("Could not resolve action handler %r", handler)
        return None


def run_action(request, key):
    """Run the configured action and return its response, or raise 404."""
    handler = resolve_action(key)
    if handler is None:
        raise Http404(f"Unknown action: {key!r}")
    return handler(request, request.POST)
