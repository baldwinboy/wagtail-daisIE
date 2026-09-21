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


def get_action_config():
    return getattr(settings, SETTING_NAME, {}) or {}


def get_action_choices():
    """Choices callable for admin blocks (lazy; never queries)."""
    choices = []
    for key, config in get_action_config().items():
        label = config.get("label", key) if isinstance(config, dict) else key
        choices.append((key, label))
    return choices


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
