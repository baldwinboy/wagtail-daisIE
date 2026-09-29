"""Inject runtime CSS for arbitrary colour utilities.

The committed stylesheet covers everything enumerable at build time. Arbitrary
colours such as ``bg-[#0080ff]`` are unpredictable, so this middleware scans the
rendered HTML for them and injects the handful of rules they need into the
document head. Staying in the initial HTML keeps it render-blocking (no FOUC).

Degrades gracefully: any failure logs a warning and leaves the response alone.
"""

from __future__ import annotations

import logging

from django.core.cache import cache


logger = logging.getLogger(__name__)

#: How long generated CSS is cached (seconds).
CACHE_TIMEOUT = 60 * 60


class ArbitraryCSSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        content_type = response.get("Content-Type", "")
        if "text/html" not in content_type or getattr(response, "streaming", False):
            return response
        if not hasattr(response, "content"):
            return response
        try:
            from .arbitrary import build_color_css, cache_key, extract_color_tokens

            charset = response.charset or "utf-8"
            html = response.content.decode(charset)
            tokens = extract_color_tokens(html)
            if not tokens:
                return response
            key = cache_key(tokens)
            css = cache.get(key)
            if css is None:
                css = build_color_css(tokens)
                cache.set(key, css, CACHE_TIMEOUT)
            if not css:
                return response
            tag = f'<style id="daisie-arbitrary-css">{css}</style>'
            if "</head>" in html:
                html = html.replace("</head>", f"{tag}\n</head>", 1)
            else:
                html = f"{tag}\n{html}"
            response.content = html.encode(charset)
            response["Content-Length"] = len(response.content)
        except Exception:  # pragma: no cover - never break a response
            logger.warning("Arbitrary colour CSS injection failed", exc_info=True)
        return response
