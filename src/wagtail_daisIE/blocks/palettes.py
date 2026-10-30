"""Named child-block palettes for the finite layout tiers.

The palettes are acyclic by construction:

* ``inline`` contains inline elements only.
* ``inline_layout`` adds the inline counterparts of the common layouts.
* ``layout`` adds specialized containers and data blocks.

Full common layouts use ``layout``; their inline counterparts use ``inline``.
Specialized containers and calendar event designs use ``inline_layout``. This
keeps the editor block-definition graph finite without depth limits or cyclic
telepath references.
"""

from __future__ import annotations

from collections.abc import Callable

from django.core.exceptions import ImproperlyConfigured
from wagtail import blocks


type PaletteEntry = tuple[str, blocks.Block]
type Palette = tuple[PaletteEntry, ...]

_PALETTES: dict[str, Palette] = {}


#: Top-level block keys that are inline elements (no layout recursion).
#: Full layouts, inline layout counterparts, specialized containers and data
#: blocks are deliberately excluded.
INLINE_BLOCK_KEYS = frozenset(
    {
        "breadcrumbs",
        "image",
        "header",
        "text",
        "rich_text",
        "button",
        "inline_link",
        "embed",
        "icon",
        "copyright",
        "blockquote",
        "badge",
        "kbd",
        "divider",
        "avatar",
        "stat",
        "countdown",
        "skeleton",
        "text_rotate",
        "chat",
        "timeline",
        "diff",
        "hover_gallery",
        "hover_3d",
        "mask",
        "swap",
        "table",
        "marquee",
        "dropdown",
        "link_list",
        "pagination",
        "fab",
        "filter",
        "join",
        "mockup_code",
        "status",
        "progress",
        "radial_progress",
        "loading",
        "tooltip",
        "steps",
        "input",
        "textarea",
        "select",
        "checkbox",
        "toggle",
        "radio",
        "range",
        "rating",
        "file",
        "fieldset",
        "newsletter",
        "action",
    }
)


def _all_content_blocks() -> list[PaletteEntry]:
    from .content import ALL_CONTENT_BLOCKS

    return list(ALL_CONTENT_BLOCKS)


def _pick(entries: list[PaletteEntry], keys: frozenset[str]) -> list[PaletteEntry]:
    return [(name, block) for name, block in entries if name in keys]


def _inline() -> list[PaletteEntry]:
    from ..dynamic.action_blocks import ActionFormBlock
    from .inputs import AutocompleteSelectMultipleBlock

    return [
        *_pick(_all_content_blocks(), INLINE_BLOCK_KEYS),
        ("action_form", ActionFormBlock()),
        ("autocomplete", AutocompleteSelectMultipleBlock()),
    ]


def _inline_layout() -> list[PaletteEntry]:
    from .cards import InlineCardBlock
    from .layout import ColumnInlineBlock, GridInlineBlock, RowInlineBlock
    from .layout_components import (
        AuraInlineBlock,
        DrawerInlineBlock,
        HeroInlineBlock,
        IndicatorInlineBlock,
        StackInlineBlock,
        TabsInlineBlock,
    )
    from .spaced import ListInlineBlock

    return [
        *_inline(),
        ("row_inline", RowInlineBlock()),
        ("column_inline", ColumnInlineBlock()),
        ("grid_inline", GridInlineBlock()),
        ("inline_card", InlineCardBlock()),
        ("list_inline", ListInlineBlock()),
        ("stack_inline", StackInlineBlock()),
        ("aura_inline", AuraInlineBlock()),
        ("indicator_inline", IndicatorInlineBlock()),
        ("drawer_inline", DrawerInlineBlock()),
        ("hero_inline", HeroInlineBlock()),
        ("tabs_inline", TabsInlineBlock()),
    ]


def _layout() -> list[PaletteEntry]:
    from ..feeds.blocks_data import CalendarBlock, FeedBlock
    from .accordion import AccordionBlock
    from .feedback import AlertBlock, ModalBlock, ToastBlock
    from .layout_components import CarouselBlock
    from .mockups import (
        MockupBrowserBlock,
        MockupPhoneBlock,
        MockupWindowBlock,
    )
    from .reusable import ReusableBlockBlock

    return [
        *_inline_layout(),
        ("accordion", AccordionBlock()),
        ("alert", AlertBlock()),
        ("toast", ToastBlock()),
        ("modal", ModalBlock()),
        ("carousel", CarouselBlock()),
        ("mockup_browser", MockupBrowserBlock()),
        ("mockup_window", MockupWindowBlock()),
        ("mockup_phone", MockupPhoneBlock()),
        ("feed", FeedBlock()),
        ("calendar", CalendarBlock()),
        ("reusable", ReusableBlockBlock()),
    ]


def _layout_item() -> PaletteEntry:
    from .layout import LayoutItemBlock

    return ("layout_item", LayoutItemBlock())


def _inline_layout_item() -> PaletteEntry:
    from .layout import InlineLayoutItemBlock

    return ("layout_item_inline", InlineLayoutItemBlock())


def _layout_container_content() -> list[PaletteEntry]:
    return [*_layout(), _layout_item()]


def _inline_layout_container_content() -> list[PaletteEntry]:
    return [*_inline(), _inline_layout_item()]


def _dropdown() -> list[PaletteEntry]:
    from .display import DividerBlock
    from .icons import IconChooserBlock
    from .inline import HeaderBlock, InlineTextBlock
    from .link import ButtonBlock, LabelLinkBlock
    from .spaced import LinkListBlock

    return [
        ("link", LabelLinkBlock()),
        ("text", InlineTextBlock()),
        ("header", HeaderBlock()),
        ("divider", DividerBlock()),
        ("button", ButtonBlock()),
        ("icon", IconChooserBlock()),
        ("link_list", LinkListBlock()),
    ]


def _marquee() -> list[PaletteEntry]:
    from .display import BadgeBlock
    from .icons import IconChooserBlock
    from .inline import HeaderBlock, InlineTextBlock
    from .link import ButtonBlock, InlineLinkBlock
    from .media import InlineImageBlock

    return [
        ("text", InlineTextBlock()),
        ("image", InlineImageBlock()),
        ("header", HeaderBlock()),
        ("icon", IconChooserBlock()),
        ("badge", BadgeBlock()),
        ("inline_link", InlineLinkBlock()),
        ("button", ButtonBlock()),
    ]


_BUILDERS: dict[str, Callable[[], list[PaletteEntry]]] = {
    "inline": _inline,
    "inline_layout": _inline_layout,
    "layout": _layout,
    "row_content": _layout_container_content,
    "column_content": _layout_container_content,
    "grid_content": _layout_container_content,
    "inline_row_content": _inline_layout_container_content,
    "inline_column_content": _inline_layout_container_content,
    "inline_grid_content": _inline_layout_container_content,
    "dropdown": _dropdown,
    "marquee": _marquee,
}


def get_palette(key: str) -> Palette:
    """Return the resolved palette for ``key``, building it on first use."""
    palette = _PALETTES.get(key)
    if palette is not None:
        return palette

    try:
        builder = _BUILDERS[key]
    except KeyError as exc:
        raise ImproperlyConfigured(
            f"Unknown palette {key!r}. Available palettes: "
            f"{', '.join(sorted(_BUILDERS))}."
        ) from exc

    entries = tuple(builder())
    names = [name for name, _block in entries]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ImproperlyConfigured(
            f"Palette {key!r} contains duplicate block types: {', '.join(duplicates)}."
        )

    _PALETTES[key] = entries
    return entries


def palette_keys(key: str) -> list[str]:
    """Return the block type keys in a palette, in editor order."""
    return [name for name, _block in get_palette(key)]


def resolved_palette_keys() -> tuple[str, ...]:
    """Return the palettes resolved so far (for import-hygiene tests)."""
    return tuple(_PALETTES)


__all__ = [
    "INLINE_BLOCK_KEYS",
    "Palette",
    "PaletteEntry",
    "get_palette",
    "palette_keys",
    "resolved_palette_keys",
]
