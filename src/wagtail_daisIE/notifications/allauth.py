"""django-allauth account-adapter mixin.

Add the mixin *before* ``DefaultAccountAdapter`` so DaisyUI templates render
allauth emails while every other adapter override (signup rules, redirects,
verification) is preserved::

    from allauth.account.adapter import DefaultAccountAdapter
    from wagtail_daisIE.notifications.allauth import DaisyUIAccountAdapterMixin


    class AccountAdapter(DaisyUIAccountAdapterMixin, DefaultAccountAdapter):
        def is_open_for_signup(self, request): ...

allauth is an optional dependency and is never imported here.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


logger = logging.getLogger(__name__)


def get_active_override(template_prefix):
    """Return the active override for ``template_prefix`` with a template."""
    from .models import AllauthEmailOverride

    return (
        AllauthEmailOverride.objects.select_related("email_template")
        .filter(
            template_prefix=template_prefix,
            is_active=True,
            email_template__isnull=False,
        )
        .first()
    )


def build_allauth_payload(context):
    """Return the ``payload`` mapping exposed to the email template."""
    payload = {}
    for key, value in (context or {}).items():
        if key == "request":
            continue
        payload[key] = value
    return payload


def render_allauth_message(adapter, template_prefix, email, context, headers=None):
    """Render a DaisyUI email for an allauth prefix, or ``None`` if unmapped."""
    override = get_active_override(template_prefix)
    if override is None:
        return None

    template = override.email_template
    recipients = [email] if isinstance(email, str) else list(email or [])
    recipients = [address for address in recipients if address]
    if not recipients:
        return None

    from_email = None
    get_from_email = getattr(adapter, "get_from_email", None)
    if callable(get_from_email):
        try:
            from_email = get_from_email()
        except Exception:  # pragma: no cover - defensive
            from_email = None
    from_email = from_email or settings.DEFAULT_FROM_EMAIL

    payload = build_allauth_payload(context)
    recipient = (context or {}).get("user") or recipients[0]

    rendered = template.render(
        payload=payload,
        recipient=recipient,
        from_email=from_email,
    )

    subject = rendered.subject
    formatter = getattr(adapter, "format_email_subject", None)
    if callable(formatter):
        try:
            subject = formatter(subject)
        except Exception:  # pragma: no cover - defensive
            logger.debug("format_email_subject failed", exc_info=True)

    message = EmailMultiAlternatives(
        subject,
        rendered.text,
        from_email,
        recipients,
        headers=headers or None,
    )
    if rendered.html:
        message.attach_alternative(rendered.html, "text/html")
    return message


class DaisyUIAccountAdapterMixin:
    """Route allauth emails through DaisyUI ``EmailTemplate`` snippets."""

    def render_mail(self, template_prefix, email, context, headers=None):
        message = render_allauth_message(self, template_prefix, email, context, headers)
        if message is not None:
            return message
        return super().render_mail(template_prefix, email, context, headers)
