"""Dispatch bridge events to DaisyUI email templates.

``connect_signals`` is called from ``AppConfig.ready`` and wires Django signals
declared in ``WAGTAIL_DAISIE_NOTIFICATION_BRIDGES`` to :func:`dispatch`.
Projects whose events travel on a custom bus call :func:`dispatch` directly,
passing the bus payload as ``source``.
"""

from __future__ import annotations

import logging

from collections.abc import Mapping

from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q

from .conf import get_dedupe_timeout, get_from_email
from .placeholders import register_placeholder_provider
from .registry import (
    Bridge,
    get_bridge,
    get_bridge_placeholder_groups,
    get_bridges,
)


logger = logging.getLogger(__name__)


class UnknownBridgeError(KeyError):
    """Raised when ``dispatch`` is called with an unconfigured event key."""

    def __init__(self, event_key):
        super().__init__(f"Unknown notification bridge: {event_key!r}")


# Register bridge placeholders with the admin help panel.
register_placeholder_provider(get_bridge_placeholder_groups)


# --- Recipients -------------------------------------------------------------


def normalize_recipients(value):
    """Coerce a recipients value into a list of candidate recipients."""
    if value is None:
        return []
    if isinstance(value, (str, int)) or hasattr(value, "pk"):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def resolve_recipient(item):
    """Resolve a user id / user / email into a usable recipient."""
    if item is None:
        return None
    if isinstance(item, bool):
        return None
    if isinstance(item, int):
        from django.contrib.auth import get_user_model

        return get_user_model().objects.filter(pk=item).first()
    return item


def recipient_email(item):
    if item is None:
        return ""
    if isinstance(item, str):
        return item
    return getattr(item, "email", "") or ""


# --- Context / recipients ---------------------------------------------------


def _as_mapping(value):
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def build_bridge_context(bridge: Bridge, source):
    """Return the ``payload`` context for ``bridge`` from ``source``."""
    if bridge.context_builder is not None:
        try:
            result = bridge.context_builder(source)
        except TypeError:
            result = bridge.context_builder(**source)
        mapping = _as_mapping(result)
        if mapping:
            return mapping
    return _infer_context(source)


def _infer_context(source):
    for candidate in (source.get("payload"), source.get("context")):
        mapping = _as_mapping(candidate)
        if mapping:
            return mapping
    return {}


def build_bridge_recipients(bridge: Bridge, source, context):
    """Resolve the recipients for ``bridge``."""
    raw = None
    if bridge.recipients_builder is not None:
        raw = bridge.recipients_builder(source)
    else:
        for candidate in (source.get("payload"), source.get("context"), context):
            mapping = _as_mapping(candidate)
            if not mapping:
                continue
            raw = mapping.get("recipient_user_ids") or mapping.get("recipients")
            if raw:
                break
    resolved = []
    for item in normalize_recipients(raw):
        recipient = resolve_recipient(item)
        if recipient is not None:
            resolved.append(recipient)
    return resolved


# --- Template / sending -----------------------------------------------------


def get_email_template(bridge: Bridge):
    """Return the :class:`EmailTemplate` a bridge targets, if any."""
    if not bridge.template:
        return None
    from ..emails.models import EmailTemplate

    return (
        EmailTemplate.objects.filter(
            Q(name=bridge.template) | Q(template_key=bridge.template)
        )
        .order_by("pk")
        .first()
    )


def _claim_event(event_key, event_ref):
    key = f"wagtail_daisIE.notification.{event_key}.{event_ref}"
    return cache.add(key, True, timeout=get_dedupe_timeout())


def dispatch(event_key, *, source=None, event_ref=""):
    """Render and send the emails configured for ``event_key``.

    Parameters
    ----------
    event_key:
        A key from ``WAGTAIL_DAISIE_NOTIFICATION_BRIDGES``.
    source:
        Context for the bridge. For Django signals this is filled in
        automatically; for a custom bus pass the event/payload here.
    event_ref:
        Optional stable reference used to deduplicate repeated dispatches.

    Returns the list of recipient email addresses that were sent to.
    """
    bridge = get_bridge(event_key)
    if bridge is None:
        raise UnknownBridgeError(event_key)

    source = dict(source or {})
    if event_ref and not _claim_event(event_key, event_ref):
        logger.info("Skipping duplicate bridge event %s (%s)", event_key, event_ref)
        return []

    template = get_email_template(bridge)
    if template is None:
        logger.warning(
            "No email template %r configured for bridge %r",
            bridge.template,
            event_key,
        )
        return []

    context = build_bridge_context(bridge, source)
    recipients = build_bridge_recipients(bridge, source, context)
    if not recipients:
        logger.info("Bridge %r resolved no recipients", event_key)
        return []

    from_email = get_from_email()
    sent = []
    for recipient in recipients:
        email = recipient_email(recipient)
        if not email:
            continue
        try:
            rendered = template.render(
                payload=context,
                recipient=recipient,
                from_email=from_email,
            )
            message = EmailMultiAlternatives(
                rendered.subject,
                rendered.text,
                from_email,
                [email],
            )
            if rendered.html:
                message.attach_alternative(rendered.html, "text/html")
            message.send()
        except Exception:
            logger.exception("Bridge %r failed sending to %s", event_key, email)
            continue
        sent.append(email)
    return sent


# --- Signal wiring ----------------------------------------------------------


def make_receiver(bridge: Bridge):
    """Build a Django signal receiver that dispatches ``bridge``."""

    def receiver(sender, **kwargs):
        source = {"sender": sender, **kwargs}
        try:
            dispatch(bridge.key, source=source)
        except Exception:
            logger.exception("Notification bridge %r receiver failed", bridge.key)

    receiver.__name__ = f"daisie_bridge_{bridge.key}"
    return receiver


def _dispatch_uid(bridge):
    return f"wagtail_daisIE.bridge.{bridge.key}"


def connect_signals():
    """Connect every bridge that declares a Django signal."""
    connected = 0
    for bridge in get_bridges().values():
        signal = bridge.signal
        if signal is None:
            continue
        signal.connect(
            make_receiver(bridge),
            sender=bridge.sender,
            dispatch_uid=_dispatch_uid(bridge),
            weak=False,
        )
        connected += 1
    return connected


def disconnect_signals():
    """Disconnect every bridge receiver (used by tests/reloads)."""
    for bridge in get_bridges().values():
        signal = bridge.signal
        if signal is None:
            continue
        signal.disconnect(sender=bridge.sender, dispatch_uid=_dispatch_uid(bridge))
