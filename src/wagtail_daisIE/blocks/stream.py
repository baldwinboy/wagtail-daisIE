"""Stream blocks whose children come from a named palette.

A palette stream block resolves its child blocks lazily. Declaring it as a
declarative subclass (rather than passing ``local_blocks``) keeps it compact in
migrations: it serialises as ``wagtail_daisIE.blockref.RegisteredBlock`` and the
live class rebuilds the current palette when the migration is loaded.

The palettes themselves are finite and acyclic; see ``blocks/palettes.py`` and
``docs/block-palettes.md``.
"""

from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks.compact import DaisieStreamBlock
from .palettes import get_palette


class PaletteStreamBlock(DaisieStreamBlock):
    """A stream whose children are resolved from :mod:`blocks.palettes`."""

    palette: str = ""

    def __init__(self, *args, **kwargs):
        if args or kwargs:
            raise TypeError(
                "PaletteStreamBlock blocks are declarative; set `palette` and "
                "`Meta` on a subclass instead of passing constructor arguments."
            )
        super().__init__(local_blocks=None)
        # BaseStreamBlock.__init__ assigns an empty child_blocks dict through
        # the property setter; clear it so the first access resolves the palette.
        self.__dict__.pop("_resolved_child_blocks", None)

    @property
    def child_blocks(self) -> dict[str, blocks.Block]:
        children = self.__dict__.get("_resolved_child_blocks")
        if children is None:
            if not self.palette:
                raise ImproperlyConfigured(
                    f"{type(self).__name__} must define a `palette` attribute."
                )
            children = {}
            for name, block in get_palette(self.palette):
                block.set_name(name)
                children[name] = block
            self.__dict__["_resolved_child_blocks"] = children
        return children

    @child_blocks.setter
    def child_blocks(self, value) -> None:
        # BaseStreamBlock.__init__ writes its (empty) base_blocks copy here.
        self.__dict__["_resolved_child_blocks"] = value or None

    def deconstruct(self):
        """Serialise as a stable reference, without touching the palette."""
        return (
            "wagtail_daisIE.blockref.RegisteredBlock",
            [self._migration_key],
            {},
        )

    class Meta:
        abstract = True


class InlineStreamBlock(PaletteStreamBlock):
    """Tier 0: inline elements only."""

    palette = "inline"

    class Meta:
        label = _("Inline content")


class InlineLayoutStreamBlock(PaletteStreamBlock):
    """Tier 1: inline elements and inline layout counterparts."""

    palette = "inline_layout"

    class Meta:
        label = _("Layout content")


class LayoutStreamBlock(PaletteStreamBlock):
    """Tier 2: full layouts may contain inline layouts, specialized
    containers and data blocks, but never another full layout."""

    palette = "layout"

    class Meta:
        label = _("Content")


class CardContentStreamBlock(LayoutStreamBlock):
    class Meta:
        label = _("Card content")


class InlineCardContentStreamBlock(InlineStreamBlock):
    class Meta:
        label = _("Card content")


class AccordionItemContentStreamBlock(InlineLayoutStreamBlock):
    class Meta:
        label = _("Accordion item content")


class DrawerSideStreamBlock(LayoutStreamBlock):
    class Meta:
        label = _("Sidebar")


class TabContentStreamBlock(LayoutStreamBlock):
    class Meta:
        label = _("Tab content")


class DropdownItemsStreamBlock(PaletteStreamBlock):
    palette = "dropdown"

    class Meta:
        label = _("Items")


class MarqueeContentStreamBlock(PaletteStreamBlock):
    palette = "marquee"

    class Meta:
        label = _("Marquee content")


class SlideContentStreamBlock(InlineLayoutStreamBlock):
    class Meta:
        label = _("Slide content")
        required = False


class FeedbackBodyStreamBlock(InlineLayoutStreamBlock):
    class Meta:
        label = _("Body")
        required = False


__all__ = [
    "AccordionItemContentStreamBlock",
    "CardContentStreamBlock",
    "DrawerSideStreamBlock",
    "DropdownItemsStreamBlock",
    "FeedbackBodyStreamBlock",
    "InlineCardContentStreamBlock",
    "InlineLayoutStreamBlock",
    "InlineStreamBlock",
    "LayoutStreamBlock",
    "MarqueeContentStreamBlock",
    "PaletteStreamBlock",
    "SlideContentStreamBlock",
    "TabContentStreamBlock",
]
