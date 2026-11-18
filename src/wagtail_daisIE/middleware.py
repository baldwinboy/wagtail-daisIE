"""Compile Tailwind CSS for rendered HTML through a JS artifact handshake.

Python extracts the page's classes, stores the compilation input in the shared
cache and injects a per-page JSON config. The browser fetches or compiles the
stylesheet and fills the placeholder. Python never writes CSS into the HTML.
"""

from __future__ import annotations

import gzip
import logging
import zlib

from django.http import HttpResponse

from .tailwindcss import orchestration
from .tailwindcss.compiler import TailwindCompilationError


logger = logging.getLogger(__name__)


class TailwindCSSMiddleware:
    """Resolve a compilation plan and inject the client configuration."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not self._should_process(response):
            return response

        html_text = self._decode(response)
        if html_text is None:
            return response

        try:
            updated = orchestration.prepare_html(
                request,
                html_text,
                fragment=bool(getattr(request, "htmx", False)),
            )
        except TailwindCompilationError:
            logger.warning("JIT CSS configuration failed", exc_info=True)
            return response
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
