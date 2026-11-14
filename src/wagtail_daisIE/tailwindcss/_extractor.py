"""Oxide-compatible Tailwind candidate parsing.

This is a structural port of the candidate grammar in
``tailwindcss/crates/oxide/src/extractor`` (Tailwind CSS v4.3.3). Rendered
HTML already gives us whitespace-delimited tokens, so the scanner,
pre-processors and sub-candidate recovery are intentionally not ported: each
token is parsed or rejected as a whole.

The parser returns :class:`ParsedCandidate` values that keep the variant chain,
the utility, the utility's base/value split and the optional modifier. The
compiler uses that structure instead of re-splitting class strings.
"""

from __future__ import annotations

import re

from collections.abc import Iterator
from dataclasses import dataclass


_MAX_BRACKET_DEPTH = 32

_WHITESPACE = frozenset(" \t\n\r\f")
_QUOTES = frozenset("\"'`")
_BRACKET_OPEN = frozenset("([{")
_BRACKET_CLOSE = frozenset(")]}")

# token boundaries only; rendered class values are already HTML-decoded
_SPLIT_RE = re.compile(r"[ \t\n\r\f]+")


@dataclass(frozen=True, slots=True)
class ParsedCandidate:
    """A validated Tailwind candidate and its structural pieces."""

    raw: str
    variants: tuple[str, ...]
    utility: str
    base: str
    value: str | None
    modifier: str | None
    important_before: bool = False
    important_after: bool = False


def parse_classnames(value: str) -> Iterator[ParsedCandidate]:
    """Yield parsed candidates from a whitespace-separated class value."""
    for token in _SPLIT_RE.split(value.strip()):
        if not token:
            continue
        candidate = parse_candidate(token)
        if candidate is not None:
            yield candidate


def parse_candidate(token: str) -> ParsedCandidate | None:
    """Parse one token using the Tailwind candidate grammar."""
    length = len(token)
    if not length:
        return None

    index = 0
    variants: list[str] = []
    while index < length:
        end = _parse_variant(token, index)
        if end is None:
            break
        variants.append(token[index:end])
        index = end

    if index >= length:
        return None

    parsed = _parse_utility(token, index)
    if parsed is None:
        return None

    end, utility_end, modifier, important_before, important_after = parsed
    if end != length:
        return None

    utility_start = index + 1 if important_before else index
    utility = token[utility_start:utility_end]
    base, value = _split_utility(utility)
    return ParsedCandidate(
        raw=token,
        variants=tuple(variants),
        utility=utility,
        base=base,
        value=value,
        modifier=modifier,
        important_before=important_before,
        important_after=important_after,
    )


# ---------------------------------------------------------------------------
# Character helpers
# ---------------------------------------------------------------------------


def _at(text: str, index: int) -> str:
    return text[index] if 0 <= index < len(text) else "\0"


def _is_whitespace(char: str) -> bool:
    return char in _WHITESPACE


def _is_lower(char: str) -> bool:
    return "a" <= char <= "z"


def _is_upper(char: str) -> bool:
    return "A" <= char <= "Z"


def _is_alpha(char: str) -> bool:
    return _is_lower(char) or _is_upper(char)


def _is_digit(char: str) -> bool:
    return "0" <= char <= "9"


def _is_alnum(char: str) -> bool:
    return _is_alpha(char) or _is_digit(char)


def _is_non_ascii(char: str) -> bool:
    return bool(char) and ord(char) >= 0x80


# ---------------------------------------------------------------------------
# Variants
# ---------------------------------------------------------------------------


def _parse_variant(text: str, index: int) -> int | None:
    if index >= len(text):
        return None
    if text[index] == "[":
        end = _parse_arbitrary_value(text, index)
        if end is None or _at(text, end) != ":":
            return None
        return end + 1
    return _parse_named_variant(text, index)


def _parse_named_variant(text: str, index: int) -> int | None:
    char = text[index]
    if char == "*" or _is_lower(char):
        if _at(text, index + 1) == ":":
            return index + 2
        return _parse_named_variant_body(text, index + 1)
    if _is_digit(char) or char == "@":
        return _parse_named_variant_body(text, index + 1)
    return None


def _parse_named_variant_body(text: str, index: int) -> int | None:
    length = len(text)
    while index < length:
        char = text[index]
        if char == ":":
            return index + 1
        if char == "-":
            following = _at(text, index + 1)
            if following == "[":
                end = _parse_arbitrary_value(text, index + 1)
                return _finish_variant_arbitrary(text, end)
            if following == "(":
                end = _parse_arbitrary_variable(text, index + 1)
                return _finish_variant_arbitrary(text, end)
            if _is_alpha(following) or _is_digit(following) or following == "-":
                index += 1
                continue
            return None
        if char == "_":
            following = _at(text, index + 1)
            if _is_alnum(following) or following in "-_":
                index += 1
                continue
            return None
        if char == "[":
            end = _parse_arbitrary_value(text, index)
            return _finish_variant_arbitrary(text, end)
        if char in "*" or _is_alnum(char):
            index += 1
            continue
        if char == "/":
            end = _parse_modifier(text, index)
            if end is None or _at(text, end) != ":":
                return None
            return end + 1
        if char == ".":
            if not (
                _is_digit(_at(text, index - 1)) and _is_digit(_at(text, index + 1))
            ):
                return None
            index += 1
            continue
        return None
    return None


def _finish_variant_arbitrary(text: str, end: int | None) -> int | None:
    if end is None:
        return None
    following = _at(text, end)
    if following == ":":
        return end + 1
    if following == "/":
        modifier_end = _parse_modifier(text, end)
        if modifier_end is None or _at(text, modifier_end) != ":":
            return None
        return modifier_end + 1
    return None


# ---------------------------------------------------------------------------
# Utilities and modifiers
# ---------------------------------------------------------------------------


def _parse_utility(
    text: str, index: int
) -> tuple[int, int, str | None, bool, bool] | None:
    """Return ``(end, utility_end, modifier, important_before, important_after)``."""
    length = len(text)
    important_before = False
    if text[index] == "!":
        important_before = True
        index += 1
        if index >= length:
            return None

    if text[index] == "[":
        utility_end = _parse_arbitrary_property(text, index)
    else:
        utility_end = _parse_named_utility(text, index)
    if utility_end is None:
        return None
    index = utility_end

    modifier: str | None = None
    if _at(text, index) == "/":
        modifier_end = _parse_modifier(text, index)
        if modifier_end is None:
            return None
        modifier = text[index:modifier_end]
        index = modifier_end

    important_after = False
    if _at(text, index) == "!":
        if important_before:
            return None
        important_after = True
        index += 1

    return index, utility_end, modifier, important_before, important_after


def _parse_named_utility(text: str, index: int) -> int | None:
    length = len(text)
    start = index
    char = text[index]
    if char == "-":
        if not _is_lower(_at(text, index + 1)):
            return None
        index += 1
    elif char == "@":
        index += 1
    elif _is_lower(char):
        index += 1
    else:
        return None

    while index < length:
        char = text[index]
        if _is_alpha(char):
            index += 1
            continue
        if char == "-":
            following = _at(text, index + 1)
            if following == "[":
                return _parse_arbitrary_value(text, index + 1)
            if following == "(":
                return _parse_arbitrary_variable(text, index + 1)
            if _is_alnum(following) or following == "-":
                index += 1
                continue
            return None
        if char == "_":
            following = _at(text, index + 1)
            if _is_alnum(following) or following == "_":
                index += 1
                continue
            return None
        if char == ".":
            if not (
                _is_digit(_at(text, index - 1)) and _is_digit(_at(text, index + 1))
            ):
                return None
            index += 1
            continue
        if _is_digit(char):
            previous = _at(text, index - 1)
            if not (_is_alpha(previous) or _is_digit(previous) or previous in "-_."):
                return None
            following = _at(text, index + 1)
            if following == "%":
                index += 1
                continue
            if not (_is_alnum(following) or following in "._-"):
                return index + 1
            index += 1
            continue
        if char == "%":
            if not _is_digit(_at(text, index - 1)):
                return None
            return index + 1
        break

    # ``start`` is kept for readability of the grammar's start rules.
    _ = start
    return index


def _parse_modifier(text: str, index: int) -> int | None:
    if _at(text, index) != "/":
        return None
    index += 1
    following = _at(text, index)
    if following == "[":
        return _parse_arbitrary_value(text, index)
    if following == "(":
        return _parse_arbitrary_variable(text, index)
    if not _is_alnum(following):
        return None
    while index < len(text):
        char = text[index]
        if _is_alnum(char) or char in "-_.":
            index += 1
            continue
        break
    return index


# ---------------------------------------------------------------------------
# Arbitrary values, properties and variables
# ---------------------------------------------------------------------------


def _parse_arbitrary_value(text: str, index: int) -> int | None:
    if _at(text, index) != "[":
        return None
    return _parse_balanced_value(text, index + 1, property_value=False)


def _parse_arbitrary_property(text: str, index: int) -> int | None:
    if _at(text, index) != "[":
        return None
    index += 1
    property_start = index
    if index >= len(text):
        return None

    if text[index] == "-" and _at(text, index + 1) == "-":
        end = _parse_css_variable(text, index)
        if end is None or _at(text, end) != ":":
            return None
        value_start = end + 1
    else:
        value_start = None
        while index < len(text):
            char = text[index]
            if _is_lower(char) or char == "-":
                index += 1
                continue
            if char == ":" and index > property_start:
                value_start = index + 1
                break
            return None
        if value_start is None:
            return None

    return _parse_balanced_value(text, value_start, property_value=True)


def _parse_css_variable(text: str, index: int) -> int | None:
    if text[index : index + 2] != "--":
        return None
    index += 2
    seen = False
    while index < len(text):
        char = text[index]
        if char == "\\":
            following = _at(text, index + 1)
            if _is_whitespace(following) or following == "\0":
                return None
            index += 2
            seen = True
            continue
        if _is_alnum(char) or char in "-_" or _is_non_ascii(char):
            index += 1
            seen = True
            continue
        break
    return index if seen else None


def _parse_arbitrary_variable(text: str, index: int) -> int | None:
    if _at(text, index) != "(":
        return None
    index += 1
    following = _at(text, index)

    if text[index : index + 2] == "--":
        end = _parse_css_variable(text, index)
        if end is None:
            return None
        index = end
    elif _is_lower(following):
        while index < len(text):
            char = text[index]
            if _is_lower(char) or char == "-":
                index += 1
                continue
            if char == ":" and text[index + 1 : index + 3] == "--":
                index += 1
                end = _parse_css_variable(text, index)
                if end is None:
                    return None
                index = end
                break
            return None
        else:
            return None
    else:
        return None

    following = _at(text, index)
    if following == ")":
        return index + 1
    if following == ",":
        return _parse_variable_fallback(text, index + 1)
    return None


def _parse_variable_fallback(text: str, index: int) -> int | None:
    start = index
    stack: list[str] = []
    while index < len(text):
        char = text[index]
        if char == "\\":
            following = _at(text, index + 1)
            if _is_whitespace(following) or following == "\0":
                return None
            index += 2
            continue
        if char in _BRACKET_OPEN:
            if len(stack) >= _MAX_BRACKET_DEPTH:
                return None
            stack.append(_matching_close(char))
            index += 1
            continue
        if char in _BRACKET_CLOSE:
            if char == ")" and not stack:
                return index + 1 if index > start else None
            if not stack or stack.pop() != char:
                return None
            index += 1
            continue
        if char in _QUOTES:
            end = _parse_string(text, index)
            if end is None:
                return None
            index = end
            continue
        if _is_whitespace(char):
            return None
        if char == "$" and _at(text, index + 1) == "{":
            return None
        index += 1
    return None


def _parse_balanced_value(text: str, index: int, *, property_value: bool) -> int | None:
    start = index
    stack: list[str] = []
    while index < len(text):
        char = text[index]
        if char == "\\":
            following = _at(text, index + 1)
            if _is_whitespace(following) or following == "\0":
                return None
            index += 2
            continue
        if char in _BRACKET_OPEN:
            if len(stack) >= _MAX_BRACKET_DEPTH:
                return None
            stack.append(_matching_close(char))
            index += 1
            continue
        if char in _BRACKET_CLOSE:
            if char == "]" and not stack:
                return index + 1 if index > start else None
            if not stack or stack.pop() != char:
                return None
            index += 1
            continue
        if char in _QUOTES:
            end = _parse_string(text, index)
            if end is None:
                return None
            index = end
            continue
        if _is_whitespace(char):
            return None
        if char == "$" and _at(text, index + 1) == "{":
            return None
        if property_value and not stack:
            if char in ":!":
                return None
            if char == "/" and index == start:
                return None
        index += 1
    return None


def _parse_string(text: str, index: int) -> int | None:
    quote = text[index]
    index += 1
    while index < len(text):
        char = text[index]
        if char == "\\":
            following = _at(text, index + 1)
            if _is_whitespace(following) or following == "\0":
                return None
            index += 2
            continue
        if char == quote:
            return index + 1
        if _is_whitespace(char):
            return None
        index += 1
    return None


def _matching_close(char: str) -> str:
    return {"(": ")", "[": "]", "{": "}"}[char]


# ---------------------------------------------------------------------------
# Compaction support
# ---------------------------------------------------------------------------


def _split_utility(utility: str) -> tuple[str, str | None]:
    """Split a named utility at its last top-level dash."""
    if utility.startswith("["):
        return utility, None

    depth = 0
    quote: str | None = None
    escaped = False
    last = -1
    for index, char in enumerate(utility):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if quote is not None:
            if char == quote:
                quote = None
            continue
        if char in _QUOTES:
            quote = char
            continue
        if char in _BRACKET_OPEN:
            depth += 1
            continue
        if char in _BRACKET_CLOSE:
            depth -= 1
            continue
        if char == "-" and depth == 0:
            last = index

    if 0 < last < len(utility) - 1:
        return utility[:last], utility[last + 1 :]
    return utility, None
