"""Runtime guards for data-driven block recursion.

Static containers nest only as deeply as their stored content, but data-driven
blocks re-expand a stored design for every item they render. A feed whose item
design contains that same feed, a calendar that renders itself in one of its
event cards, or a reusable block that references itself through a container
would render forever.

The guard below tracks the chain of data blocks currently rendering. It blocks a
second occurrence of the same token in one chain, logs a warning, and leaves the
nested block empty. Sibling blocks are unaffected because the token is removed
when rendering finishes.
"""

from __future__ import annotations

import logging

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from wagtail.blocks.stream_block import StreamValue
from wagtail.blocks.struct_block import StructValue


logger = logging.getLogger(__name__)

_RENDER_CHAIN: ContextVar[tuple[tuple[Any, ...], ...]] = ContextVar(
    "daisie_render_chain",
    default=(),
)


@contextmanager
def guard_render(*token: Any, context: dict | None = None) -> Iterator[bool]:
    """Allow a data block to render unless it already appears in the chain."""
    chain = _RENDER_CHAIN.get()
    if token in chain:
        if context is not None:
            context["recursion_blocked"] = True
        logger.warning(
            "Daisie block recursion blocked",
            extra={"block_token": token},
        )
        yield False
        return

    reset = _RENDER_CHAIN.set((*chain, token))
    try:
        yield True
    finally:
        _RENDER_CHAIN.reset(reset)


def iter_nested_stream_blocks(
    value: Any,
    *,
    include_structs: bool = False,
    skip: Any = None,
) -> Iterator[tuple[str | None, Any]]:
    """Yield ``(block_type, value)`` for every stream child in ``value``.

    Walks ``StreamValue``, ``StructValue``, dicts and lists so validation can
    detect a data block referenced from inside its own design, even through a
    container. Raw values are handled as well as bound ones.

    When ``include_structs`` is true, every struct/dict value is yielded too
    (with ``block_type`` set to ``None``) so callers can inspect nested struct
    fields. ``skip`` is an optional callable ``skip(key, child, parent)`` that
    prevents descending into a specific mapping value.
    """
    yield from _walk(value, set(), include_structs=include_structs, skip=skip)


def _walk(
    value: Any,
    seen: set[int],
    *,
    include_structs: bool = False,
    skip: Any = None,
) -> Iterator[tuple[str | None, Any]]:
    if isinstance(value, (StreamValue, StructValue, dict, list, tuple)):
        marker = id(value)
        if marker in seen:
            return
        seen.add(marker)

    if isinstance(value, StreamValue):
        for child in value:
            yield child.block_type, child.value
            yield from _walk(
                child.value,
                seen,
                include_structs=include_structs,
                skip=skip,
            )
    elif isinstance(value, StructValue):
        if include_structs:
            yield None, value
        for key, child in value.items():
            if skip is not None and skip(key, child, value):
                continue
            yield from _walk(
                child,
                seen,
                include_structs=include_structs,
                skip=skip,
            )
    elif isinstance(value, dict):
        if include_structs:
            yield None, value
        for key, child in value.items():
            if skip is not None and skip(key, child, value):
                continue
            yield from _walk(
                child,
                seen,
                include_structs=include_structs,
                skip=skip,
            )
    elif isinstance(value, (list, tuple)):
        for child in value:
            if isinstance(child, dict) and "type" in child and "value" in child:
                yield child["type"], child["value"]
            yield from _walk(
                child,
                seen,
                include_structs=include_structs,
                skip=skip,
            )


__all__ = ["guard_render", "iter_nested_stream_blocks"]
