"""Runtime Tailwind + DaisyUI compiler for rendered HTML.

The middleware hands this module a rendered document. It extracts the class
tokens that are actually present, compacts them into ``@source inline``
patterns, builds a Tailwind input stylesheet from the package's CSS sources,
compiles it through either the configured safe server or the local
``django-tailwind-cli`` binary, and caches the result by class set.

Only candidates that appear in a rendered ``class`` attribute (or in a
``data-daisie-selected-class`` attribute used by the feed controller) are
compiled. Runtime-only classes must therefore be present in one of those
attributes.
"""

from __future__ import annotations

import hashlib
import logging
import re
import subprocess
import tempfile

from collections import defaultdict
from collections.abc import Iterable, Sequence
from importlib.resources import files
from pathlib import Path

import lxml.etree as etree
import lxml.html as lxml_html
import requests

from django.conf import settings
from django.core.cache import cache
from django.utils.html import format_html
from django.utils.safestring import SafeString

from ._extractor import ParsedCandidate, parse_candidate


logger = logging.getLogger(__name__)

JIT_PLACEHOLDER_ID = "daisyui-jit-styles"
CACHE_EXPIRY = 86_400 * 7  # 1 week
CACHE_VERSION = "v1"

CSS_SOURCE_DIR = (
    files("wagtail_daisIE") / "static" / "wagtail_daisIE" / "css" / "tailwind"
)

#: Frontend CSS sources appended to every compiled stylesheet.
CUSTOM_CSS_FILES = (
    "typography.css",
    "file-picker.css",
    "marquee.css",
    "menu.css",
    "richtext.css",
    "visibility.css",
)

#: Attributes that can contain runtime-applied classes.
_CLASS_ATTRIBUTES = ("class", "data-daisie-selected-class")

#: Package-owned classes whose CSS is always shipped by the custom CSS sources.
_SKIP_PREFIXES = ("daisie", "daisyui")

#: Classes that should never be sent to Tailwind.
_SKIP_SUFFIXES = ("block-branding",)

_PLACEHOLDER_RE = re.compile(
    rf'(<style\b[^>]*\bid\s*=\s*(["\']){re.escape(JIT_PLACEHOLDER_ID)}\2[^>]*>)'
    r"(.*?)(</style\s*>)",
    re.IGNORECASE | re.DOTALL,
)

_BRACE_UNSAFE = frozenset(",{}\\")


#: DaisyUI class prefix -> component name. Longest prefixes win.
DAISYUI_MAP = {
    "alert": "alert",
    "aura": "aura",
    "avatar": "avatar",
    "badge": "badge",
    "breadcrumbs": "breadcrumbs",
    "btn": "button",
    "cally": "calendar",
    "card": "card",
    "carousel": "carousel",
    "chat": "chat",
    "checkbox": "checkbox",
    "collapse": "collapse",
    "countdown": "countdown",
    "diff": "diff",
    "divider": "divider",
    "dock": "dock",
    "drawer": "drawer",
    "dropdown": "dropdown",
    "fab": "fab",
    "fieldset": "fieldset",
    "file-input": "fileinput",
    "filter": "filter",
    "footer": "footer",
    "hero": "hero",
    "hover-3d": "hover3d",
    "hover-gallery": "hovergallery",
    "indicator": "indicator",
    "input": "input",
    "join": "join",
    "kbd": "kbd",
    "label": "label",
    "link": "link",
    "list": "list",
    "loading": "loading",
    "mask": "mask",
    "megamenu": "megamenu",
    "menu": "menu",
    "mockup-browser": "mockup",
    "mockup-code": "mockup",
    "mockup-phone": "mockup",
    "mockup-window": "mockup",
    "modal": "modal",
    "navbar": "navbar",
    "otp": "otp",
    "progress": "progress",
    "radial-progress": "radialprogress",
    "radio": "radio",
    "range": "range",
    "rating": "rating",
    "select": "select",
    "skeleton": "skeleton",
    "stack": "stack",
    "stat": "stat",
    "stats": "stat",
    "status": "status",
    "step": "steps",
    "steps": "steps",
    "swap": "swap",
    "tab": "tab",
    "table": "table",
    "tabs": "tab",
    "textarea": "textarea",
    "text-rotate": "textrotate",
    "timeline": "timeline",
    "toast": "toast",
    "toggle": "toggle",
    "tooltip": "tooltip",
    "validator": "validator",
}

_DAISYUI_KEYS = tuple(sorted(DAISYUI_MAP, key=len, reverse=True))
_DAISYUI_COMPONENTS = tuple(sorted(set(DAISYUI_MAP.values())))


class TailwindCompilationError(Exception):
    """Raised when runtime CSS compilation fails."""


# ---------------------------------------------------------------------------
# Placeholder
# ---------------------------------------------------------------------------


def placeholder_html() -> SafeString:
    """Return the JIT stylesheet placeholder element."""
    return format_html('<style id="{}"></style>', JIT_PLACEHOLDER_ID)


def inject_stylesheet(
    html_text: str,
    stylesheet: str,
    *,
    fragment: bool = False,
) -> str | None:
    """Fill every JIT placeholder, or prepend fragment CSS.

    Returns ``None`` when a full document has no placeholder.
    """
    found = False

    def replace(match: re.Match[str]) -> str:
        nonlocal found
        found = True
        return f"{match.group(1)}{stylesheet}{match.group(4)}"

    updated = _PLACEHOLDER_RE.sub(replace, html_text)
    if found:
        return updated
    if fragment:
        return f"<style data-daisie-jit>{stylesheet}</style>\n{html_text}"
    return None


# ---------------------------------------------------------------------------
# HTML -> candidates
# ---------------------------------------------------------------------------


def compile_html(
    html_text: str,
    session: requests.Session,
    *,
    fragment: bool = False,
) -> str | None:
    """Compile the CSS needed by a rendered document or fragment."""
    if not fragment and JIT_PLACEHOLDER_ID not in html_text:
        return None
    if "class" not in html_text.lower():
        return None

    classnames = _extract_class_names(html_text, fragment=fragment)
    if not classnames:
        return None
    return compile_classnames(classnames, session, fragment=fragment)


def compile_classnames(
    classnames: Iterable[str],
    session: requests.Session,
    *,
    fragment: bool = False,
) -> str | None:
    """Compile CSS for a set of raw class names."""
    names = sorted({name for name in classnames if _is_runtime_class(name)})
    if not names:
        return None

    mode = "fragment" if fragment else "full"
    cache_key = _cache_key(mode, names)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    candidates = [
        candidate for name in names if (candidate := parse_candidate(name)) is not None
    ]
    if not candidates:
        return None

    try:
        stylesheet = _build_stylesheet(
            _daisyui_components(candidates),
            _compact_classnames(candidates),
            fragment=fragment,
        )
    except OSError as exc:
        raise TailwindCompilationError("Could not read the CSS sources") from exc

    compiled = _compile_stylesheet(stylesheet, session)
    if not compiled:
        return None
    _cache_set(cache_key, compiled)
    return compiled


def _extract_class_names(html_text: str, *, fragment: bool) -> set[str]:
    try:
        if fragment:
            try:
                root = lxml_html.fragment_fromstring(html_text, create_parent="div")
            except (etree.ParserError, etree.XMLSyntaxError, ValueError):
                root = lxml_html.document_fromstring(html_text)
        else:
            root = lxml_html.document_fromstring(html_text)
    except (etree.ParserError, etree.XMLSyntaxError, ValueError):
        return set()

    if root is None:
        return set()

    names: set[str] = set()
    for element in root.iter():
        for attribute in _CLASS_ATTRIBUTES:
            value = element.get(attribute)
            if not value:
                continue
            names.update(value.split())
    return names


def _is_runtime_class(name: str) -> bool:
    return (
        bool(name)
        and not name.startswith(_SKIP_PREFIXES)
        and not name.endswith(_SKIP_SUFFIXES)
    )


# ---------------------------------------------------------------------------
# Compaction
# ---------------------------------------------------------------------------


def _compact_classnames(candidates: Sequence[ParsedCandidate]) -> list[str]:
    """Compact parsed candidates into the smallest safe inline patterns."""
    prefix_by_member: dict[tuple, set[str]] = defaultdict(set)
    for candidate in candidates:
        prefix = "".join(candidate.variants)
        member = (
            candidate.base,
            candidate.value,
            candidate.modifier,
            candidate.important_before,
            candidate.important_after,
        )
        prefix_by_member[member].add(prefix)

    modifier_groups: dict[tuple, set[str | None]] = defaultdict(set)
    for (base, value, modifier, before, after), prefixes in prefix_by_member.items():
        key = (
            base,
            value,
            modifier is not None,
            frozenset(prefixes),
            before,
            after,
        )
        modifier_groups[key].add(modifier[1:] if modifier else None)

    final_groups: dict[tuple, set[str | None]] = defaultdict(set)
    for (
        base,
        value,
        has_modifier,
        prefixes,
        before,
        after,
    ), modifiers in modifier_groups.items():
        key = (
            base,
            value is not None,
            has_modifier,
            prefixes,
            frozenset(modifiers),
            before,
            after,
        )
        final_groups[key].add(value)

    patterns: set[str] = set()
    for (
        base,
        has_value,
        has_modifier,
        prefixes,
        modifiers,
        before,
        after,
    ), values in final_groups.items():
        value_text = _format_alternatives(
            {value for value in values if value is not None}, "-"
        )
        modifier_text = _format_alternatives(
            {modifier for modifier in modifiers if modifier is not None}, "/"
        )

        prefix_text = _format_prefixes(prefixes)
        unsafe = (
            _contains_brace_unsafe(base)
            or (value_text is None and has_value)
            or (modifier_text is None and has_modifier)
            or (len(prefixes) > 1 and any(_contains_brace_unsafe(p) for p in prefixes))
        )

        if not unsafe:
            patterns.add(
                _render_candidate(
                    prefix_text,
                    base,
                    value_text or "",
                    modifier_text or "",
                    before,
                    after,
                )
            )
            continue

        for prefix in prefixes:
            for value in values if has_value else {None}:
                for modifier in modifiers if has_modifier else {None}:
                    patterns.add(
                        _render_candidate(
                            prefix,
                            base,
                            f"-{value}" if value is not None else "",
                            f"/{modifier}" if modifier is not None else "",
                            before,
                            after,
                        )
                    )

    return sorted(patterns)


def _format_prefixes(prefixes: frozenset[str]) -> str:
    if prefixes == frozenset({""}):
        return ""
    if len(prefixes) == 1:
        return next(iter(prefixes))
    return "{" + ",".join(sorted(prefixes)) + "}"


def _format_alternatives(values: set[str], prefix: str) -> str | None:
    if not values:
        return ""
    if len(values) == 1:
        return prefix + next(iter(values))
    if any(_contains_brace_unsafe(value) for value in values):
        return None
    return prefix + "{" + ",".join(sorted(values)) + "}"


def _contains_brace_unsafe(value: str) -> bool:
    return any(char in _BRACE_UNSAFE for char in value)


def _render_candidate(
    prefix: str,
    base: str,
    value_text: str,
    modifier_text: str,
    important_before: bool,
    important_after: bool,
) -> str:
    return (
        f"{prefix}{'!' if important_before else ''}{base}{value_text}"
        f"{modifier_text}{'!' if important_after else ''}"
    )


# ---------------------------------------------------------------------------
# DaisyUI detection
# ---------------------------------------------------------------------------


def _daisyui_components(candidates: Sequence[ParsedCandidate]) -> set[str]:
    components: set[str] = set()
    for candidate in candidates:
        if candidate.utility.startswith("["):
            continue
        for key in _DAISYUI_KEYS:
            if candidate.utility == key or candidate.utility.startswith(f"{key}-"):
                components.add(DAISYUI_MAP[key])
                break
    return components


# ---------------------------------------------------------------------------
# Stylesheet assembly
# ---------------------------------------------------------------------------


def _build_stylesheet(
    components: set[str],
    patterns: Sequence[str],
    *,
    fragment: bool,
) -> str:
    lines: list[str] = []
    if fragment:
        lines.append("@layer theme, base, components, utilities;\n")
        lines.append("@import 'tailwindcss/theme.css' layer(theme);\n")
        lines.append("@import 'tailwindcss/utilities.css' layer(utilities);\n")
    else:
        lines.append("@import 'tailwindcss' source(none);\n")
    lines.append('@plugin "@tailwindcss/typography";\n')
    lines.extend(_format_source_inline(pattern) for pattern in patterns)
    lines.append(_read_css("typography.css") + "\n")
    lines.append('@plugin "daisyui" {')
    if components:
        lines.append("\n\tinclude: " + ", ".join(sorted(components)) + ";")
    else:
        lines.append("\n\texclude: " + ", ".join(_DAISYUI_COMPONENTS) + ";")
    lines.append("\n}\n")
    for name in CUSTOM_CSS_FILES:
        if name != "typography.css":
            lines.append(_read_css(name) + "\n")
    return "".join(lines)


def _format_source_inline(pattern: str) -> str:
    return f'@source inline("{_css_string(pattern)}");\n'


def _css_string(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\A ")
        .replace("\r", "\\D ")
        .replace("\f", "\\C ")
    )


def _read_css(name: str) -> str:
    return (CSS_SOURCE_DIR / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------


def _compile_stylesheet(stylesheet: str, session: requests.Session) -> str:
    api = getattr(settings, "TAILWIND_CSS_API", "")
    timeout = float(getattr(settings, "TAILWIND_CSS_TIMEOUT", 30))
    if api:
        return _safe_compile_stylesheet(stylesheet, session, api, timeout)
    return _unsafe_compile_stylesheet(stylesheet, timeout)


def _unsafe_compile_stylesheet(stylesheet: str, timeout: float) -> str:
    try:
        from django_tailwind_cli.config import (
            ConfigurationError,
            CSSEntry,
            get_config,
        )
    except ImportError as exc:  # pragma: no cover - configuration error
        raise TailwindCompilationError(
            "Unsafe Tailwind compilation requires django-tailwind-cli; "
            "install it or set TAILWIND_CSS_API."
        ) from exc

    try:
        minify = bool(getattr(settings, "TAILWIND_CLI_AUTOMATIC_MINIFY", True))
        config = get_config()
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.css"
            output_path = Path(tmp) / "output.css"
            input_path.write_text(stylesheet, encoding="utf-8")
            entry = CSSEntry(
                name="daisie-jit",
                src_css=input_path,
                dist_css=output_path,
                dist_css_base=tmp,
            )
            command = config.get_build_cmd(entry, minify=minify)
            subprocess.run(  # noqa: S603 - command comes from the configured CLI
                command,
                cwd=getattr(settings, "BASE_DIR", None),
                check=True,
                timeout=timeout,
            )
            return output_path.read_text(encoding="utf-8")
    except (OSError, subprocess.SubprocessError, ConfigurationError, ValueError) as exc:
        raise TailwindCompilationError("Unsafe Tailwind compilation failed") from exc


def _safe_compile_stylesheet(
    stylesheet: str,
    session: requests.Session,
    api: str,
    timeout: float,
) -> str:
    try:
        response = session.post(
            api,
            json={"stylesheet": stylesheet},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise TailwindCompilationError("Safe Tailwind compilation failed") from exc

    compiled = data.get("stylesheet") if isinstance(data, dict) else None
    if not isinstance(compiled, str):
        raise TailwindCompilationError(
            "Safe Tailwind compilation returned no stylesheet"
        )
    return compiled


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


def _cache_key(mode: str, names: Sequence[str]) -> str:
    digest = hashlib.sha256("\0".join(names).encode("utf-8")).hexdigest()
    return f"wagtail_daisIE:tailwind:{CACHE_VERSION}:{mode}:{digest}"


def _cache_get(key: str) -> str | None:
    try:
        return cache.get(key)
    except Exception:  # pragma: no cover - cache backend boundary
        logger.warning("Tailwind CSS cache read failed", exc_info=True)
        return None


def _cache_set(key: str, value: str) -> None:
    try:
        cache.set(key, value, timeout=CACHE_EXPIRY)
    except Exception:  # pragma: no cover - cache backend boundary
        logger.warning("Tailwind CSS cache write failed", exc_info=True)


__all__ = [
    "CACHE_EXPIRY",
    "JIT_PLACEHOLDER_ID",
    "TailwindCompilationError",
    "compile_classnames",
    "compile_html",
    "inject_stylesheet",
    "placeholder_html",
]
