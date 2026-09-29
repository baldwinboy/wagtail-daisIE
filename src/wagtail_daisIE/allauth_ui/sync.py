"""Generate and check the package's allauth account template overrides.

The package overrides every django-allauth **account** template that defines a
``{% block content %}`` so an admin-designed :class:`AllauthPageOverride` can
replace the page content. Each override keeps the upstream content verbatim as
a fallback (between the ``daisie:verbatim`` markers) and delegates to
``{% daisie_allauth_page %}`` when an override is active.

Running ``manage.py check_allauth_templates`` reports drift against the
installed allauth; ``--write`` regenerates the overrides after an upgrade.

Only the ``account`` view set is covered.
"""

from __future__ import annotations

import re

from pathlib import Path


BLOCK_RE = re.compile(r"\{%\s*(block|endblock)\b[^%]*%\}")
CONTENT_OPENERS = ("{% block content %}", "{% block content %}\n")
LOAD_LINE = "{% load allauth_ui %}\n"


def allauth_account_dir() -> Path | None:
    """Return the installed django-allauth ``account`` template directory."""
    try:
        import allauth
    except ImportError:  # pragma: no cover - allauth is optional
        return None
    root = Path(allauth.__file__).resolve().parent / "templates" / "account"
    return root if root.is_dir() else None


def package_account_dir() -> Path:
    return Path(__file__).resolve().parent / "templates" / "account"


def _content_bounds(source: str):
    """Return ``(open_start, inner_start, inner_end, close_end)`` or ``None``."""
    open_start = source.find("{% block content %}")
    if open_start == -1:
        return None
    inner_start = open_start + len("{% block content %}")
    depth = 0
    for match in BLOCK_RE.finditer(source, open_start):
        if match.group(1) == "block":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return open_start, inner_start, match.start(), match.end()
    return None


def build_override(source: str) -> str:
    """Return the package override template for an upstream ``source``."""
    bounds = _content_bounds(source)
    if bounds is None:
        raise ValueError("no content block")
    open_start, inner_start, inner_end, close_end = bounds
    opener = source[open_start:inner_start]
    closer = source[inner_end:close_end]
    inner = source[inner_start:inner_end]

    before = source[:open_start]
    if "allauth_ui" not in before:
        before = before.rstrip("\n") + "\n" + LOAD_LINE
    after = source[close_end:]

    wrapped = (
        f"{opener}\n"
        "{% if daisie_allauth_page_active %}{% daisie_allauth_page %}"
        "{% else %}\n"
        "{# daisie:verbatim:start #}\n"
        f"{inner.strip()}\n"
        "{# daisie:verbatim:end #}\n"
        "{% endif %}"
        f"{closer}"
    )
    return f"{before}{wrapped}{after}"


def iter_targets():
    """Yield ``(relpath, source, override)`` for every account template."""
    account_dir = allauth_account_dir()
    if account_dir is None:
        return
    for path in sorted(account_dir.rglob("*.html")):
        source = path.read_text(encoding="utf-8")
        if "{% block content %}" not in source:
            continue
        try:
            override = build_override(source)
        except ValueError:  # pragma: no cover - defensive
            continue
        yield path.relative_to(account_dir), source, override


def sync(write=False):
    """Return a list of ``(relpath, expected, actual)`` mismatches.

    When ``write`` is true, write (or update) every override and return ``[]``.
    """
    mismatches = []
    target_dir = package_account_dir()
    for relpath, _source, expected in iter_targets():
        destination = target_dir / relpath
        actual = destination.read_text(encoding="utf-8") if destination.exists() else ""
        if actual != expected:
            if write:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(expected, encoding="utf-8")
            else:
                mismatches.append((str(relpath), expected, actual))
    return mismatches


__all__ = ["allauth_account_dir", "build_override", "iter_targets", "sync"]
