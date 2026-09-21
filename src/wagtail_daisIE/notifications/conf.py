"""Settings access for notification bridges."""

from __future__ import annotations

from django.conf import settings


BRIDGES_SETTING = "WAGTAIL_DAISIE_NOTIFICATION_BRIDGES"
FROM_EMAIL_SETTING = "WAGTAIL_DAISIE_NOTIFICATION_FROM_EMAIL"
DEDUPE_TIMEOUT_SETTING = "WAGTAIL_DAISIE_NOTIFICATION_DEDUPE_TIMEOUT"

DEFAULT_DEDUPE_TIMEOUT = 3600


def get_bridge_config():
    """Return the raw ``WAGTAIL_DAISIE_NOTIFICATION_BRIDGES`` mapping."""
    return getattr(settings, BRIDGES_SETTING, {}) or {}


def get_from_email():
    """Return the default ``From:`` address for bridge emails."""
    return getattr(settings, FROM_EMAIL_SETTING, None) or settings.DEFAULT_FROM_EMAIL


def get_dedupe_timeout():
    """Return how long ``event_ref`` values are remembered for deduplication."""
    return getattr(settings, DEDUPE_TIMEOUT_SETTING, DEFAULT_DEDUPE_TIMEOUT)
