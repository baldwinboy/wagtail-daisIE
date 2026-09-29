"""Registry for optional block contributions from feature apps.

The core content and menu streams are defined statically, but optional apps
(such as ``notifications``) may contribute blocks. Those apps register their
blocks here at import time, guarded by an ``INSTALLED_APPS`` check so the core
streams stay importable without them.
"""

from __future__ import annotations

from typing import Any


_content: list[tuple[str, Any]] = []
_menu: list[tuple[str, Any]] = []


def register_content_block(name: str, block: Any) -> None:
    """Append a named block to the page-content stream contributions."""
    _content.append((name, block))


def register_menu_block(name: str, block: Any) -> None:
    """Append a named block to the menu-item stream contributions."""
    _menu.append((name, block))


def content_block_contributions() -> list[tuple[str, Any]]:
    return list(_content)


def menu_block_contributions() -> list[tuple[str, Any]]:
    return list(_menu)
