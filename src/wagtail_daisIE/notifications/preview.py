"""Fake render context for email template previews.

Preview renders should show representative values instead of empty strings.
This module supplies a sample recipient, synthesises ``payload.*`` keys found
in the template, and stubs configured context models that cannot be resolved.
"""

from __future__ import annotations

import re

from types import SimpleNamespace

from ..dynamic.registry import get_context_models
from ..dynamic.resolvers import resolve_context_models
from .context import Recipient, build_context


_PAYLOAD_RE = re.compile(r"{{\s*payload\.(?P<name>[A-Za-z0-9_]+)")


def _sample_value(name):
    return f"Sample {str(name).replace('_', ' ').title()}"


def _payload_samples(*texts):
    payload = {}
    for text in texts:
        for match in _PAYLOAD_RE.finditer(str(text or "")):
            name = match.group("name")
            payload.setdefault(name, _sample_value(name))
    return payload


def _stub_model(config):
    """Return a namespace whose attributes render as readable samples."""
    obj = SimpleNamespace()
    for doc in config.field_docs(limit=None):
        setattr(obj, doc["name"], _sample_value(doc["name"]))
    obj.pk = 1
    obj.url = f"/{config.key}/"
    return obj


def sample_recipient():
    """Return a readable sample :class:`Recipient`."""
    recipient = Recipient(user=None, email="ada@example.com", name="Ada Lovelace")
    recipient.first_name = "Ada"
    recipient.last_name = "Lovelace"
    recipient.username = "ada"
    recipient.pk = 1
    return recipient


def build_preview_context(
    *, request=None, subject="", preheader="", content="", payload=None
):
    """Build a placeholder context with fake values for a preview render."""
    samples = _payload_samples(subject, preheader, content)
    samples.update(payload or {})
    context = build_context(
        request=request,
        recipient=sample_recipient(),
        payload=samples,
    )
    resolved = resolve_context_models(request)
    for key, config in get_context_models().items():
        if resolved.get(key) is None:
            resolved[key] = _stub_model(config)
    context.update(resolved)
    return context
