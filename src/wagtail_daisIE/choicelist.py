"""Lazy choice lists that serialize compactly in migrations.

``ChoiceList`` is a callable ``list`` subclass whose ``deconstruct`` serialises
to a short registry key (``get_choice_list("<KEY>")``) instead of the full option
list. Wagtail stores a callable ``choices`` argument by reference, so the options
stay out of the frozen StreamField ``block_lookup`` in migrations.
"""

import sys

from importlib import import_module


#: Short key -> fully-qualified import path of the module-level choice list.
_CHOICE_REGISTRY: dict[str, str] = {}


def get_choice_list(key):
    """Return the choice list registered under ``key`` (called from migrations)."""
    module_name, attribute = _CHOICE_REGISTRY[key].rsplit(".", 1)
    return getattr(import_module(module_name), attribute)


class ChoiceList(list):
    """A static choices list that serialises compactly in migrations.

    It is a ``list`` (so ``isinstance`` checks and ``", ".join`` callers keep
    working) and callable (so Wagtail stores the callable by reference rather
    than materialising the options into the frozen StreamField ``block_lookup``).
    """

    def __init__(self, choices, name, key=None):
        super().__init__(choices)
        module = sys._getframe(1).f_globals.get("__name__", "")
        self.import_path = f"{module}.{name}" if module else name
        self.key = key or name
        existing = _CHOICE_REGISTRY.get(self.key)
        if existing is not None and existing != self.import_path:
            raise ValueError(
                f"ChoiceList key {self.key!r} is already registered to "
                f"{existing!r}; pass an explicit key=."
            )
        _CHOICE_REGISTRY[self.key] = self.import_path

    def __call__(self):
        return list(self)

    def deconstruct(self):
        return ("wagtail_daisIE.choicelist.get_choice_list", [self.key], {})
