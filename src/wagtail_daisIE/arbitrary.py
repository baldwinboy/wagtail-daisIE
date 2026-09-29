"""Runtime CSS for arbitrary colour utilities.

The committed stylesheet only contains the classes that are enumerable ahead
of time. Arbitrary colours (``bg-[#0080ff]``, ``decoration-[#0080ff]`` and
their ``hover:``/``active:`` variants) are unpredictable, so the few rules they
need are generated at request time and injected into the document head (see
:class:`wagtail_daisIE.middleware.ArbitraryCSSMiddleware`).

Only the colour prefixes accepted by ``SwatchChoiceField`` are handled; the
mapping is deterministic, so this is not a Tailwind re-implementation.
"""

from __future__ import annotations

import hashlib
import re


#: Arbitrary colour utilities accepted on the design blocks.
COLOR_PATTERN = re.compile(
    r"((?:hover:|active:)?)(bg|text|border|decoration)-\[(#[0-9a-fA-F]{3,8})\]"
)

#: Utility prefix -> CSS property.
PROPERTY = {
    "bg": "background-color",
    "text": "color",
    "border": "border-color",
    "decoration": "text-decoration-color",
}

#: Variant prefix -> pseudo-class.
VARIANT_PSEUDO = {"": "", "hover:": ":hover", "active:": ":active"}

#: Cache key prefix for the generated arbitrary-colour CSS.
CACHE_PREFIX = "daisie:arbitrary:css:"


def _escape_class(name):
    return re.sub(r"([:\[\]#])", r"\\\1", name)


def extract_color_tokens(html):
    """Return distinct ``(variant, prefix, hex)`` arbitrary colour tokens."""
    return set(COLOR_PATTERN.findall(html or ""))


def build_color_css(tokens):
    """Return the CSS rules for a set of ``(variant, prefix, hex)`` tokens."""
    rules = []
    for variant, prefix, value in sorted(tokens):
        prop = PROPERTY.get(prefix)
        if not prop:
            continue
        value = value.lower()
        selector = "." + _escape_class(f"{variant}{prefix}-[{value}]")
        selector += VARIANT_PSEUDO.get(variant, "")
        rules.append(f"{selector}{{{prop}:{value}}}")
    return "\n".join(rules)


def cache_key(tokens):
    digest = hashlib.sha256(repr(sorted(tokens)).encode()).hexdigest()
    return f"{CACHE_PREFIX}{digest}"
