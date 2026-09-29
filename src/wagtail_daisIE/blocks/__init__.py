"""Public block composition package.

The heavy composition modules (``menu_items`` and ``content``) are imported
lazily. Importing them eagerly would create an import cycle: ``cards`` needs
``dynamic.action_blocks``, which needs ``blocks.link``; loading ``blocks.link``
runs this package's ``__init__`` first, so the package must not pull in
``menu_items``/``cards`` at import time.
"""

from importlib import import_module

from ..base_blocks import (
    BackgroundLayerBlock,
    BackgroundStreamBlock,
    GradientStopBlock,
    LinkDestinationBlock,
    ThemedBlock,
    ThemedTypographyBlock,
)
from ..icons.blocks import IconChooserBlock
from .base import BorderBlock, ColorChoiceBlock


#: Public name -> the submodule it lives in (imported on first access).
_LAZY_EXPORTS = {
    "MENU_ITEM_BLOCKS": ".menu_items",
    "MenuBranding": ".menu_items",
    "MenuItemStreamBlock": ".menu_items",
    "MenuLogo": ".menu_items",
    "MenuNewsletterBlock": ".menu_items",
    "MenuSearchBoxBlock": ".menu_items",
    "ALL_CONTENT_BLOCKS": ".content",
    "AccordionBlock": ".content",
    "BlockQuote": ".content",
    "CONTENT_BLOCK": ".content",
    "CONTENT_BLOCKS": ".content",
    "LIST_CONTENT_BLOCKS": ".content",
}


def __getattr__(name):
    module_path = _LAZY_EXPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_path, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


__all__ = [
    "BackgroundLayerBlock",
    "BackgroundStreamBlock",
    "BorderBlock",
    "BlockQuote",
    "ColorChoiceBlock",
    "GradientStopBlock",
    "IconChooserBlock",
    "LinkDestinationBlock",
    "ThemedBlock",
    "ThemedTypographyBlock",
    "ALL_CONTENT_BLOCKS",
    "CONTENT_BLOCKS",
    "CONTENT_BLOCK",
    "LIST_CONTENT_BLOCKS",
    "AccordionBlock",
    "MENU_ITEM_BLOCKS",
    "MenuBranding",
    "MenuItemStreamBlock",
    "MenuLogo",
    "MenuNewsletterBlock",
    "MenuSearchBoxBlock",
]
