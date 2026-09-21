"""Render context for placeholders.

Every rendered surface (email, page, block, campaign) gets a non-negotiable
context:

* ``site`` -- the Wagtail :class:`~wagtail.models.Site` for the request (or the
  default site when there is no request);
* ``now`` -- a timezone-aware ``datetime`` so authors can format it with
  Django's ``date``/``time`` filters, e.g. ``{{ now|date:"j F Y" }}``;
* ``recipient`` / ``user`` -- the person the content is for, when known.

Nothing here queries the database at import time; site lookups happen only when
:func:`get_current_site` is called during rendering.
"""

from __future__ import annotations

import logging

from django.utils import timezone
from wagtail.models import Site


logger = logging.getLogger(__name__)


class Recipient:
    """A lightweight view of the person a message is addressed to.

    ``user`` holds the underlying object when there is one, so templates can
    reach related data (``{{ recipient.user.profile.img }}``). The flat
    attributes work for both users and bare email addresses.
    """

    def __init__(self, *, user=None, email="", name=""):
        self.user = user
        self.email = email or getattr(user, "email", "") or ""
        full_name = ""
        get_full_name = getattr(user, "get_full_name", None)
        if callable(get_full_name):
            full_name = get_full_name() or ""
        self.first_name = getattr(user, "first_name", "") or ""
        self.last_name = getattr(user, "last_name", "") or ""
        self.username = getattr(user, "username", "") or ""
        self.pk = getattr(user, "pk", None)
        self.name = name or full_name or f"{self.first_name} {self.last_name}".strip()
        if not self.name:
            self.name = self.email

    def __str__(self):
        return self.name or self.email

    def as_dict(self):
        return {
            "email": self.email,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "pk": self.pk,
        }


def recipient_from(value):
    """Coerce ``value`` (User, email string, Recipient or None) to a Recipient."""
    if value is None:
        return None
    if isinstance(value, Recipient):
        return value
    if isinstance(value, str):
        return Recipient(email=value)
    return Recipient(user=value)


def get_current_site(request=None, site=None):
    """Return the Wagtail ``Site`` for ``request``/``site``, or the default.

    Never raises: a missing site simply returns ``None`` so rendering can fall
    back gracefully during migrations, tests or detached (cron) sends.
    """
    if site is not None:
        return site
    if request is not None:
        try:
            found = Site.find_for_request(request)
        except Exception:  # pragma: no cover - defensive
            found = None
        if found is not None:
            return found
    return Site.objects.filter(is_default_site=True).first() or Site.objects.first()


def build_context(
    *, request=None, site=None, recipient=None, payload=None, user=None, now=None
):
    """Build the base placeholder context used by every renderer."""
    recipient_obj = recipient_from(recipient)
    user_obj = user
    if user_obj is None and recipient_obj is not None:
        user_obj = recipient_obj.user
    if recipient_obj is None and user_obj is not None:
        recipient_obj = recipient_from(user_obj)

    context = {
        "site": get_current_site(request, site),
        "now": now or timezone.now(),
        "payload": payload if payload is not None else {},
    }
    if recipient_obj is not None:
        context["recipient"] = recipient_obj
        context["user"] = user_obj if user_obj is not None else recipient_obj
    elif user_obj is not None:
        context["user"] = user_obj
    return context


#: Context keys that are copied from an email block's parent context so nested
#: templates keep access to the placeholder context.
PLACEHOLDER_CONTEXT_KEYS = ("payload", "recipient", "user", "site", "now")


def context_from_template_context(template_context):
    """Extract the placeholder context from a Django template ``Context``.

    Block HTML is rendered with the keys injected by
    :meth:`wagtail_daisIE.emails.models.EmailTemplate.get_mjml_context`; this
    helper picks them up and fills in defaults (``now`` and, when absent, the
    current site) so the tags also work outside the email renderer.
    """
    data = {}
    for key in PLACEHOLDER_CONTEXT_KEYS:
        try:
            value = template_context.get(key)
        except Exception:  # pragma: no cover - defensive
            value = None
        if value is not None:
            data[key] = value

    data.setdefault("payload", {})
    data.setdefault("now", timezone.now())
    if "site" not in data:
        request = None
        try:
            request = template_context.get("request")
        except Exception:  # pragma: no cover - defensive
            request = None
        data["site"] = get_current_site(request)

    # Configured context models are resolved into the render context by the
    # page/block machinery; pick them up so tags can resolve {{ key.field }}.
    from ..dynamic.context import context_model_keys

    for key in context_model_keys():
        if key in data:
            continue
        try:
            if key in template_context:
                data[key] = template_context[key]
        except Exception:  # pragma: no cover - defensive
            logger.debug("Could not read context model %r from context", key)
            continue
    return data
