"""Structural validation for stylesheets crossing a trust boundary.

This is deliberately not a CSS parser. It rejects content that could escape a
``<style>`` element or hide unbalanced input, while accepting modern Tailwind
and DaisyUI syntax such as ``@layer``, ``@property`` and ``@supports``.
"""

from __future__ import annotations

from django.conf import settings


class CssValidationError(ValueError):
    """Raised when a stylesheet fails structural validation."""


_CONTROL_ALLOWED = frozenset("\t\n\r\f")
_BRACKETS = {"(": ")", "[": "]", "{": "}"}
_CLOSERS = frozenset(_BRACKETS.values())


def validate_css(css: str, *, max_bytes: int | None = None) -> str:
    """Validate a complete stylesheet and return it unchanged."""
    if not isinstance(css, str):
        raise CssValidationError("Stylesheet must be a string.")
    if not css.strip():
        raise CssValidationError("Stylesheet is empty.")

    if max_bytes is None:
        max_bytes = int(
            getattr(settings, "WAGTAIL_DAISIE_TAILWIND_MAX_CSS_BYTES", 5_000_000)
        )
    if max_bytes > 0 and len(css.encode("utf-8")) > max_bytes:
        raise CssValidationError("Stylesheet exceeds the configured size limit.")

    lowered = css.lower()
    if "\x00" in css:
        raise CssValidationError("Stylesheet contains a NUL byte.")
    if "<script" in lowered or "</style" in lowered:
        raise CssValidationError("Stylesheet contains HTML markup.")

    for char in css:
        if ord(char) < 32 and char not in _CONTROL_ALLOWED:
            raise CssValidationError("Stylesheet contains a control character.")

    _validate_balanced(css)
    return css


def _validate_balanced(css: str) -> None:
    stack: list[str] = []
    quote: str | None = None
    in_comment = False
    escaped = False
    index = 0
    length = len(css)

    while index < length:
        char = css[index]

        if escaped:
            escaped = False
            index += 1
            continue

        if char == "\\":
            escaped = True
            index += 1
            continue

        if in_comment:
            if char == "*" and index + 1 < length and css[index + 1] == "/":
                in_comment = False
                index += 2
                continue
            index += 1
            continue

        if quote is not None:
            if char == quote:
                quote = None
            index += 1
            continue

        if char == "/" and index + 1 < length and css[index + 1] == "*":
            in_comment = True
            index += 2
            continue

        if char in {"'", '"', "`"}:
            quote = char
            index += 1
            continue

        if char in _BRACKETS:
            stack.append(_BRACKETS[char])
            index += 1
            continue

        if char in _CLOSERS:
            if not stack or stack.pop() != char:
                raise CssValidationError("Stylesheet has unbalanced brackets.")
            index += 1
            continue

        index += 1

    if in_comment or quote is not None or stack or escaped:
        raise CssValidationError("Stylesheet is not structurally complete.")
