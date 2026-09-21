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
from .menu_items import (
    MENU_ITEM_BLOCKS,
    MenuBranding,
    MenuItemStreamBlock,
    MenuLogo,
    MenuNewsletterBlock,
    MenuSearchBoxBlock,
)


# ``.content`` is imported lazily: it pulls in the data-driven blocks, which
# import this package again via ``blocks.content_blocks``.
_LAZY_CONTENT = {
    "ALL_CONTENT_BLOCKS",
    "AccordionBlock",
    "BlockQuote",
    "CONTENT_BLOCK",
    "CONTENT_BLOCKS",
    "LIST_CONTENT_BLOCKS",
}


def __getattr__(name):
    if name in _LAZY_CONTENT:
        from . import content

        return getattr(content, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
