"""Tailwind compilation API configuration and Python HTTP client."""

from __future__ import annotations

import logging
import secrets

from dataclasses import dataclass
from typing import Literal
from urllib.parse import quote, urlsplit, urlunsplit

import requests

from django.conf import settings

from .validators import CssValidationError, validate_css


logger = logging.getLogger(__name__)

Transport = Literal["http", "websocket"]

_HTTP_SCHEMES = ("http://", "https://")
_WS_SCHEMES = ("ws://", "wss://")

NONCE_PARAM = "nonce"
NONCE_BYTES = 32


def new_nonce() -> str:
    """Return a fresh 64-character hex nonce."""
    return secrets.token_hex(NONCE_BYTES)


def append_nonce(url: str, nonce: str) -> str:
    """Return ``url`` with a single fresh nonce query parameter.

    Existing query parameters are preserved exactly; an existing ``nonce``
    parameter is removed and replaced. The fragment is preserved.
    """
    parts = urlsplit(url)
    pairs = [
        pair
        for pair in parts.query.split("&")
        if pair and pair.split("=", 1)[0] != NONCE_PARAM
    ]
    pairs.append(f"{NONCE_PARAM}={quote(nonce, safe='')}")
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            "&".join(pairs),
            parts.fragment,
        )
    )


class TailwindAPIError(ValueError):
    """Raised when the configured Tailwind API is invalid."""


@dataclass(frozen=True)
class TailwindAPI:
    url: str
    transport: Transport
    token: str
    timeout: float


def get_tailwind_api() -> TailwindAPI | None:
    """Return the configured API, or ``None`` when it is absent/invalid."""
    api, _error = _coerce_api()
    return api


def tailwind_api_error() -> str | None:
    """Return a configuration error message for system checks."""
    _api, error = _coerce_api()
    return error


def js_api_config(api: TailwindAPI, *, nonce: str) -> dict[str, str] | None:
    """Return browser-safe API config with a server-built nonce URL."""
    if api.token:
        return None
    return {
        "url": append_nonce(api.url, nonce),
        "transport": api.transport,
    }


def compile_via_http(
    stylesheet: str,
    api: TailwindAPI,
    *,
    nonce: str | None = None,
) -> str:
    """Compile a stylesheet through the configured HTTP API."""
    try:
        validate_css(stylesheet)
    except CssValidationError as exc:
        raise TailwindAPIError("Tailwind input stylesheet is invalid.") from exc

    headers = {"Accept": "application/json"}
    if api.token:
        headers["Authorization"] = f"Bearer {api.token}"

    final_url = append_nonce(api.url, nonce or new_nonce())

    try:
        response = requests.post(
            final_url,
            json={"stylesheet": stylesheet},
            headers=headers,
            timeout=api.timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise TailwindAPIError("Tailwind HTTP compilation failed.") from exc

    compiled = payload.get("stylesheet") if isinstance(payload, dict) else None
    if not isinstance(compiled, str):
        raise TailwindAPIError("Tailwind HTTP API returned no stylesheet.")
    try:
        validate_css(compiled)
    except CssValidationError as exc:
        raise TailwindAPIError("Tailwind HTTP API returned invalid CSS.") from exc
    return compiled


def _coerce_api() -> tuple[TailwindAPI | None, str | None]:
    raw = getattr(settings, "TAILWIND_CSS_API", None)
    if raw in (None, "", {}):
        return None, None

    if isinstance(raw, str):
        url = raw.strip()
        if not url:
            return None, None
        transport = _transport_from_url(url)
        token = str(getattr(settings, "TAILWIND_CSS_API_TOKEN", "") or "")
        if transport is None:
            return None, "TAILWIND_CSS_API must use http(s) or ws(s)."
        try:
            timeout = _timeout(None)
        except TailwindAPIError as exc:
            return None, str(exc)
        return TailwindAPI(
            url=url, transport=transport, token=token, timeout=timeout
        ), None

    if not isinstance(raw, dict):
        return None, "TAILWIND_CSS_API must be a dict or URL string."

    url = str(raw.get("url") or "").strip()
    if not url:
        return None, "TAILWIND_CSS_API['url'] is required."

    declared = raw.get("transport")
    transport = _normalize_transport(declared) if declared else _transport_from_url(url)
    if transport is None:
        return None, "TAILWIND_CSS_API['transport'] must be http or websocket."

    if _transport_from_url(url) not in (None, transport):
        return None, "TAILWIND_CSS_API URL scheme does not match its transport."

    token = str(
        raw.get("token") or getattr(settings, "TAILWIND_CSS_API_TOKEN", "") or ""
    )
    try:
        timeout = _timeout(raw.get("timeout"))
    except TailwindAPIError as exc:
        return None, str(exc)
    return TailwindAPI(url=url, transport=transport, token=token, timeout=timeout), None


def _timeout(value: object) -> float:
    if value is None:
        value = getattr(settings, "TAILWIND_CSS_TIMEOUT", 30)
    try:
        timeout = float(value)
    except (TypeError, ValueError) as exc:
        raise TailwindAPIError("TAILWIND_CSS_TIMEOUT must be numeric.") from exc
    return timeout if timeout > 0 else 30.0


def _normalize_transport(value: object) -> Transport | None:
    text = str(value or "").strip().lower()
    if text in {"http", "https"}:
        return "http"
    if text in {"ws", "wss", "websocket"}:
        return "websocket"
    return None


def _transport_from_url(url: str) -> Transport | None:
    lowered = url.lower()
    if lowered.startswith(_HTTP_SCHEMES):
        return "http"
    if lowered.startswith(_WS_SCHEMES):
        return "websocket"
    return None
