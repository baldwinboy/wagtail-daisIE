"""Stable registry keys for compact block migration references.

Mirrors :mod:`wagtail_daisIE.choicelist`: a block's migration definition stores
only a short key, and the key resolves to the live block at migration-load time.
The key is independent of the class's module path, so moving a block does not
break migration history; renaming is handled by freezing ``Meta.migration_key``.

Like ``ChoiceList``, the registry stores an import path rather than the class
object, so re-importing or reloading a module (as the import-hygiene tests do)
overwrites the same path instead of raising a spurious duplicate-key error.
"""

from __future__ import annotations

from django.utils.module_loading import import_string
from wagtail import blocks


#: Stable key -> dotted path of the block class that rebuilds it.
_BLOCK_REGISTRY: dict[str, str] = {}


def register_block(key: str, factory: type[blocks.Block]) -> str:
    """Register ``factory`` under ``key``; reject conflicting class paths."""
    path = f"{factory.__module__}.{factory.__qualname__}"
    existing = _BLOCK_REGISTRY.get(key)
    if existing is not None and existing != path:
        raise ValueError(
            f"Block registry key {key!r} is already registered to {existing!r}. "
            "Give the class a unique Meta.migration_key (or rename it)."
        )
    _BLOCK_REGISTRY[key] = path
    return key


def get_block(key: str) -> blocks.Block:
    """Return a fresh instance of the block registered under ``key``."""
    try:
        path = _BLOCK_REGISTRY[key]
    except KeyError as exc:
        raise KeyError(
            f"No block is registered under migration key {key!r}. A block class "
            "was renamed without preserving Meta.migration_key."
        ) from exc
    return import_string(path)()


class RegisteredBlock:
    """Reconstruction hook called by ``wagtail.blocks.BlockDefinitionLookup``."""

    @classmethod
    def construct_from_lookup(cls, lookup, key):
        return get_block(key)
