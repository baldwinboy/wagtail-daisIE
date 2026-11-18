"""Content-addressed CSS artifact views."""

from __future__ import annotations

import logging

from django.http import HttpResponse
from django.views.decorators.http import require_GET

from . import artifacts


logger = logging.getLogger(__name__)

_CACHE_CONTROL = "public, max-age=31536000, immutable"


@require_GET
def artifact(request, token: str):
    """Return compiled CSS, a generic error, or 404 while still pending."""
    if not artifacts.is_valid_token(token):
        return HttpResponse(status=404)

    stylesheet = artifacts.get_output(token)
    if stylesheet is not None:
        return _css_response(stylesheet)

    error = artifacts.get_error(token)
    if error is not None:
        logger.warning("Tailwind artifact %s failed: %s", token, error)
        return HttpResponse(
            "Tailwind compilation failed.",
            status=500,
            content_type="text/plain; charset=utf-8",
        )

    return HttpResponse(status=404)


@require_GET
def input(request, token: str):
    """Return the compiled input stylesheet for browser-side API modes."""
    if not artifacts.is_valid_token(token):
        return HttpResponse(status=404)

    stylesheet = artifacts.get_input(token)
    if stylesheet is None:
        return HttpResponse(status=404)
    return _css_response(stylesheet)


def _css_response(stylesheet: str) -> HttpResponse:
    response = HttpResponse(stylesheet, content_type="text/css; charset=utf-8")
    response["Cache-Control"] = _CACHE_CONTROL
    response["X-Content-Type-Options"] = "nosniff"
    return response
