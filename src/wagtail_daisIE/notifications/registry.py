"""Registry of notification bridges.

A bridge maps a business event to a DaisyUI email template plus the callables
that turn a local signal (or a bus payload) into a context and recipients.

Projects declare bridges in settings::

    WAGTAIL_DAISIE_NOTIFICATION_BRIDGES = {
        "booking_requested": {
            "label": _("Booking requested"),
            "template": "Booking requested",
            "signal": "myapp.signals.booking_requested",
            "sender": "myapp.models.MeetingRequest",
            "context": "myapp.notifications.booking_context",
            "recipients": "myapp.notifications.booking_recipients",
            "placeholders": {"meeting_title": _("Meeting title")},
        },
    }

Everything is resolved lazily; importing this module never touches the database.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass, field

from django.apps import apps
from django.utils.module_loading import import_string

from .conf import get_bridge_config


logger = logging.getLogger(__name__)

_bridges_cache: dict[str, Bridge] | None = None


@dataclass
class Bridge:
    """One entry from ``WAGTAIL_DAISIE_NOTIFICATION_BRIDGES``."""

    key: str
    label: object
    template: str = ""
    signal_path: str = ""
    sender_path: str = ""
    context_path: str = ""
    recipients_path: str = ""
    placeholders: dict = field(default_factory=dict)
    _signal: object = field(default=None, repr=False)
    _sender: object = field(default=None, repr=False)
    _context: object = field(default=None, repr=False)
    _recipients: object = field(default=None, repr=False)
    _resolved: bool = field(default=False, repr=False)

    def __str__(self):
        return str(self.label or self.key)

    def resolve(self):
        """Resolve the dotted paths (once)."""
        if self._resolved:
            return self
        self._signal = resolve_dotted(self.signal_path, kind="signal")
        self._sender = resolve_sender(self.sender_path)
        self._context = resolve_dotted(self.context_path, kind="context")
        self._recipients = resolve_dotted(self.recipients_path, kind="recipients")
        self._resolved = True
        return self

    @property
    def signal(self):
        return self.resolve()._signal

    @property
    def sender(self):
        return self.resolve()._sender

    @property
    def context_builder(self):
        return self.resolve()._context

    @property
    def recipients_builder(self):
        return self.resolve()._recipients


def resolve_dotted(path, *, kind="callable"):
    """Resolve a dotted path to an object, warning (not raising) on failure."""
    if not path:
        return None
    try:
        return import_string(path)
    except ImportError:
        logger.warning("Could not resolve notification bridge %s %r", kind, path)
        return None


def resolve_sender(path):
    """Resolve a sender path (``app_label.ModelName`` or dotted import)."""
    if not path:
        return None
    try:
        return apps.get_model(path)
    except (LookupError, ValueError):
        pass
    try:
        return import_string(path)
    except ImportError:
        logger.warning("Could not resolve notification bridge sender %r", path)
        return None


def _build_bridge(key, raw):
    raw = dict(raw or {})
    return Bridge(
        key=key,
        label=raw.get("label") or key.replace("_", " ").title(),
        template=raw.get("template", "") or "",
        signal_path=raw.get("signal", "") or "",
        sender_path=raw.get("sender", "") or "",
        context_path=raw.get("context", "") or "",
        recipients_path=raw.get("recipients", "") or "",
        placeholders=dict(raw.get("placeholders") or {}),
    )


def get_bridges():
    """Return every configured bridge keyed by its event key."""
    global _bridges_cache
    if _bridges_cache is not None:
        return _bridges_cache

    bridges = {}
    for key, raw in get_bridge_config().items():
        if not isinstance(raw, dict):
            continue
        try:
            bridges[key] = _build_bridge(key, raw)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Invalid notification bridge config for %r", key)
    _bridges_cache = bridges
    return bridges


def reset_bridges():
    """Clear the cached registry (tests / ``override_settings``)."""
    global _bridges_cache
    _bridges_cache = None


def get_bridge(key):
    return get_bridges().get(key)


def bridges_for_template(template_name):
    """Return bridges that target ``template_name``."""
    return [
        bridge
        for bridge in get_bridges().values()
        if bridge.template and bridge.template == template_name
    ]


def get_bridge_placeholder_groups():
    """Placeholder groups (for the admin help panel) declared by bridges."""
    groups = []
    for bridge in get_bridges().values():
        if not bridge.placeholders:
            continue
        items = [
            {
                "token": f"{{{{ payload.{name} }}}}",
                "description": str(description),
            }
            for name, description in bridge.placeholders.items()
        ]
        groups.append(
            {
                "title": str(bridge.label),
                "description": f"Bridge: {bridge.key}",
                "items": items,
            }
        )
    return groups
