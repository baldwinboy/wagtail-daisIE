"""Content-addressed cache storage for Tailwind input and output CSS."""

from __future__ import annotations

import hashlib
import logging
import re

from django.conf import settings
from django.core.cache import cache
from django.urls import NoReverseMatch, reverse


logger = logging.getLogger(__name__)

CACHE_VERSION = "v2"
TOKEN_RE = re.compile(r"^[a-f0-9]{64}$")

_INPUT = "input"
_OUTPUT = "output"
_ERROR = "error"


def token_for(input_stylesheet: str) -> str:
    """Return the content-addressed token for an input stylesheet."""
    return hashlib.sha256(input_stylesheet.encode("utf-8")).hexdigest()


def is_valid_token(token: str) -> bool:
    return bool(TOKEN_RE.fullmatch(token or ""))


def store_input(input_stylesheet: str) -> str:
    token = token_for(input_stylesheet)
    _cache_set(_key(_INPUT, token), input_stylesheet, _artifact_ttl())
    return token


def get_input(token: str) -> str | None:
    if not is_valid_token(token):
        return None
    return _cache_get(_key(_INPUT, token))


def store_output(token: str, stylesheet: str) -> None:
    _cache_set(_key(_OUTPUT, token), stylesheet, _artifact_ttl())
    _cache_delete(_key(_ERROR, token))


def get_output(token: str) -> str | None:
    if not is_valid_token(token):
        return None
    return _cache_get(_key(_OUTPUT, token))


def store_error(token: str, message: str) -> None:
    _cache_set(_key(_ERROR, token), message, _error_ttl())


def get_error(token: str) -> str | None:
    if not is_valid_token(token):
        return None
    return _cache_get(_key(_ERROR, token))


def input_url(token: str) -> str:
    return _reverse("input", token)


def output_url(token: str) -> str:
    return _reverse("artifact", token)


def _reverse(name: str, token: str) -> str:
    try:
        return reverse(
            f"wagtail_daisIE_tailwind:{name}",
            kwargs={"token": token},
        )
    except NoReverseMatch:
        logger.warning(
            "The wagtail_daisIE.tailwindcss URLs are not included; "
            "add path('daisie/tailwind/', include('wagtail_daisIE.tailwindcss.urls'))."
        )
        return ""


def _key(kind: str, token: str) -> str:
    return f"wagtail_daisIE:tailwind:{CACHE_VERSION}:{kind}:{token}"


def _artifact_ttl() -> int:
    return int(getattr(settings, "WAGTAIL_DAISIE_TAILWIND_ARTIFACT_TTL", 604800))


def _error_ttl() -> int:
    return int(getattr(settings, "WAGTAIL_DAISIE_TAILWIND_ERROR_TTL", 300))


def _cache_get(key: str) -> str | None:
    try:
        value = cache.get(key)
    except Exception:  # pragma: no cover - cache backend boundary
        logger.warning("Tailwind artifact cache read failed", exc_info=True)
        return None
    return value if isinstance(value, str) else None


def _cache_set(key: str, value: str, timeout: int) -> None:
    try:
        cache.set(key, value, timeout=timeout)
    except Exception:  # pragma: no cover - cache backend boundary
        logger.warning("Tailwind artifact cache write failed", exc_info=True)


def _cache_delete(key: str) -> None:
    try:
        cache.delete(key)
    except Exception:  # pragma: no cover - cache backend boundary
        logger.warning("Tailwind artifact cache delete failed", exc_info=True)
