"""Compile Tailwind CSS for rendered HTML into the JIT placeholder.

The compiled stylesheet is cached by the set of class names on the page, so
repeated renders avoid both parsing and compilation. If compilation fails the
response is left untouched; a missing compiler must never break a page.
"""

from __future__ import annotations

import gzip
import logging
import threading
import zlib

import requests

from django.http import HttpResponse

from .tailwindcss import (
    TailwindCompilationError,
    compile_html,
    inject_stylesheet,
)


logger = logging.getLogger(__name__)

_SESSION = threading.local()


def _get_session() -> requests.Session:
    """Return a thread-local HTTP session for the safe compiler server."""
    session = getattr(_SESSION, "session", None)
    if session is None:
        session = _SESSION.session = requests.Session()
    return session


class TailwindCSSMiddleware:
    """Inject runtime-compiled Tailwind CSS into the document head."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not self._should_process(response):
            return response

        html_text = self._decode(response)
        if html_text is None:
            return response

        fragment = bool(getattr(request, "htmx", False))
        try:
            stylesheet = compile_html(
                html_text,
                _get_session(),
                fragment=fragment,
            )
        except TailwindCompilationError:
            logger.warning("JIT CSS compilation failed", exc_info=True)
            return response
        if not stylesheet:
            return response

        updated = inject_stylesheet(html_text, stylesheet, fragment=fragment)
        if updated is None:
            return response

        self._encode(response, updated)
        return response

    @staticmethod
    def _should_process(response) -> bool:
        if not isinstance(response, HttpResponse):
            return False
        if response.streaming:
            return False
        if getattr(response, "charset", None) is None:
            return False
        content_type = response.get("Content-Type", "").lower()
        return "text/html" in content_type

    @staticmethod
    def _decode(response) -> str | None:
        body = response.content
        encoding = response.get("Content-Encoding", "").lower()

        if encoding == "gzip":
            try:
                body = gzip.decompress(body)
            except OSError:
                return None
        elif encoding == "deflate":
            try:
                body = zlib.decompress(body)
            except zlib.error:
                return None
        elif encoding:  # br, zstd, etc.
            return None

        try:
            return body.decode(response.charset or "utf-8", errors="replace")
        except (LookupError, UnicodeDecodeError):
            return body.decode("utf-8", errors="replace")

    @staticmethod
    def _encode(response, html_text: str) -> None:
        encoded = html_text.encode(response.charset or "utf-8")

        encoding = response.get("Content-Encoding", "").lower()
        if encoding == "gzip":
            encoded = gzip.compress(encoded)
        elif encoding == "deflate":
            encoded = zlib.compress(encoded)

        response.content = encoded
        if "Content-Length" in response:
            response["Content-Length"] = str(len(encoded))
