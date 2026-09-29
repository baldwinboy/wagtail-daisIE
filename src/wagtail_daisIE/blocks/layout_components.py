"""Layout/decorative component blocks (stack, aura, mask, dropdown, swap)."""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.images.blocks import ImageBlock as WagtailImageBlock

from ..base_blocks import InlineMarkupBlock, ThemedBlock
from ..base_blocks.link import LinkDestinationBlock, link_url
from ..choicelist import ChoiceList
from ..choices import (
    CAROUSEL_ORIENTATION_CHOICES,
    DROPDOWN_POSITION_CHOICES,
    INDICATOR_COLOR_CHOICES,
    INDICATOR_POSITION_CHOICES,
    MASK_SHAPE_CHOICES,
    SWAP_EFFECT_CHOICES,
    TABS_PLACEMENT_CHOICES,
    TABS_SIZE_CHOICES,
    TABS_STYLE_CHOICES,
)
from ..icons.blocks import IconChooserBlock
from .inline import InlineTextBlock
from .link import LabelLinkBlock
from .spaced import LIST_CONTENT_BLOCKS, SpacedBlock


HERO_ALIGN_CHOICES = ChoiceList(
    [
        ("left", _("Left")),
        ("center", _("Center")),
    ],
    "HERO_ALIGN_CHOICES",
)
JOIN_ITEM_TYPE_CHOICES = ChoiceList(
    [
        ("button", _("Button")),
        ("input", _("Input")),
    ],
    "JOIN_ITEM_TYPE_CHOICES",
)


class StackBlock(SpacedBlock):
    class Meta:
        abstract = False
        icon = "stack"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/stack.html"
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "alignment", "audience"],
        )


class AuraBlock(SpacedBlock):
    class Meta:
        abstract = False
        icon = "pick"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/aura.html"
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "alignment", "audience"],
        )


class IndicatorBlock(SpacedBlock):
    position = blocks.ChoiceBlock(
        choices=INDICATOR_POSITION_CHOICES,
        default="indicator-top indicator-end",
    )
    item = InlineMarkupBlock(max_length=32, label=_("Indicator"))
    color = blocks.ChoiceBlock(
        choices=INDICATOR_COLOR_CHOICES, default="", required=False
    )

    class Meta:
        abstract = False
        icon = "dot"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/indicator.html"
        form_layout = blocks.BlockGroup(
            children=["item", "color", "position", "content"],
            settings=["design", "alignment", "audience"],
        )


class MaskBlock(ThemedBlock):
    image = WagtailImageBlock()
    shape = blocks.ChoiceBlock(choices=MASK_SHAPE_CHOICES, default="mask-squircle")

    class Meta:
        icon = "image"
        group = _("Media")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/mask.html"
        form_layout = blocks.BlockGroup(
            children=["image", "shape"],
            settings=["design", "audience"],
        )


class DropdownBlock(ThemedBlock):
    trigger = InlineMarkupBlock(max_length=64)
    position = blocks.ChoiceBlock(
        choices=DROPDOWN_POSITION_CHOICES,
        default="",
        required=False,
    )
    content = blocks.StreamBlock(
        [
            ("link", LabelLinkBlock()),
            ("text", InlineTextBlock()),
        ],
        label=_("Items"),
    )

    class Meta:
        icon = "arrow-down"
        group = _("Actions")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/dropdown.html"
        form_layout = blocks.BlockGroup(
            children=["trigger", "position", "content"],
            settings=["design", "audience"],
        )


class SwapBlock(ThemedBlock):
    on_text = InlineMarkupBlock(max_length=64, label=_("On"))
    off_text = InlineMarkupBlock(max_length=64, label=_("Off"))
    effect = blocks.ChoiceBlock(choices=SWAP_EFFECT_CHOICES, default="", required=False)

    class Meta:
        icon = "repeat"
        group = _("Actions")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/swap.html"
        form_layout = blocks.BlockGroup(
            children=["on_text", "off_text", "effect"],
            settings=["design", "audience"],
        )


class TabItemBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=128)
    content = blocks.StreamBlock(LIST_CONTENT_BLOCKS)

    class Meta:
        icon = "doc-full"
        label = _("Tab")
        collapsed = True


class TabsBlock(ThemedBlock):
    tabs = blocks.ListBlock(TabItemBlock())
    style = blocks.ChoiceBlock(choices=TABS_STYLE_CHOICES, default="tabs-box")
    size = blocks.ChoiceBlock(choices=TABS_SIZE_CHOICES, default="", required=False)
    placement = blocks.ChoiceBlock(
        choices=TABS_PLACEMENT_CHOICES, default="", required=False
    )

    class Meta:
        icon = "list-ul"
        group = _("Navigation")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/tabs.html"
        form_layout = blocks.BlockGroup(
            children=["tabs", "style", "size", "placement"],
            settings=["design", "audience"],
        )


class CarouselSlideBlock(blocks.StructBlock):
    image = WagtailImageBlock()
    caption = blocks.CharBlock(max_length=255, required=False, blank=True)

    class Meta:
        icon = "image"
        label = _("Slide")
        collapsed = True


class CarouselBlock(ThemedBlock):
    slides = blocks.ListBlock(CarouselSlideBlock())
    orientation = blocks.ChoiceBlock(
        choices=CAROUSEL_ORIENTATION_CHOICES,
        default="",
        required=False,
    )

    class Meta:
        icon = "image"
        group = _("Media")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/carousel.html"
        form_layout = blocks.BlockGroup(
            children=["slides", "orientation"],
            settings=["design", "audience"],
        )


class PaginationItemBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=64)
    destination = LinkDestinationBlock()

    class Meta:
        icon = "link"
        label = _("Page")
        collapsed = True


class PaginationBlock(ThemedBlock):
    pages = blocks.ListBlock(PaginationItemBlock())
    active = blocks.IntegerBlock(
        default=1, min_value=1, label=_("Active page"), help_text=_("1-based index.")
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
        active = int(value.get("active", 1) or 1)
        pages = []
        for index, page in enumerate(value.get("pages") or [], start=1):
            pages.append(
                {
                    "label": page.get("label", ""),
                    "url": link_url(page.get("destination"), context=context),
                    "active": index == active,
                }
            )
        context["pages"] = pages
        return context

    class Meta:
        icon = "arrow-right"
        group = _("Navigation")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/pagination.html"
        form_layout = blocks.BlockGroup(
            children=["pages", "active"],
            settings=["design", "audience"],
        )


class FabItemBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=64)
    icon = IconChooserBlock(required=False)
    destination = LinkDestinationBlock()

    class Meta:
        icon = "link"
        label = _("Action")
        collapsed = True


class FabBlock(ThemedBlock):
    trigger_icon = IconChooserBlock(required=False)
    trigger_label = blocks.CharBlock(max_length=64, required=False, blank=True)
    items = blocks.ListBlock(FabItemBlock(), label=_("Actions"))

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
        context["items"] = [
            {
                "label": item.get("label", ""),
                "icon": item.get("icon"),
                "url": link_url(item.get("destination"), context=context),
            }
            for item in (value.get("items") or [])
        ]
        return context

    class Meta:
        icon = "plus-inverse"
        group = _("Actions")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/fab.html"
        form_layout = blocks.BlockGroup(
            children=["trigger_icon", "trigger_label", "items"],
            settings=["design", "audience"],
        )


class HeroBlock(SpacedBlock):
    overlay = blocks.BooleanBlock(default=False, required=False)
    full_width = blocks.BooleanBlock(
        default=True,
        required=False,
        help_text=_("Break out of the page container to span the viewport."),
    )
    align = blocks.ChoiceBlock(
        choices=HERO_ALIGN_CHOICES,
        default="left",
        label=_("Content alignment"),
    )

    class Meta:
        abstract = False
        icon = "photo"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/hero.html"
        form_layout = blocks.BlockGroup(
            children=["overlay", "full_width", "align", "content"],
            settings=["design", "alignment", "audience"],
        )


class DrawerBlock(SpacedBlock):
    side = blocks.StreamBlock(LIST_CONTENT_BLOCKS, label=_("Sidebar"))

    class Meta:
        abstract = False
        icon = "bars"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/drawer.html"
        form_layout = blocks.BlockGroup(
            children=["side", "content"],
            settings=["design", "alignment", "audience"],
        )


class FilterBlock(ThemedBlock):
    name = blocks.CharBlock(
        max_length=64, required=False, blank=True, label=_("Group name")
    )
    options = blocks.ListBlock(blocks.CharBlock(max_length=64, label=_("Option")))

    class Meta:
        icon = "funnel"
        group = _("Data input")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/filter.html"
        form_layout = blocks.BlockGroup(
            children=["name", "options"],
            settings=["design", "audience"],
        )


class JoinItemBlock(blocks.StructBlock):
    type = blocks.ChoiceBlock(
        choices=JOIN_ITEM_TYPE_CHOICES,
        default="button",
    )
    text = InlineMarkupBlock(
        max_length=128, required=False, blank=True, label=_("Text / placeholder")
    )

    class Meta:
        icon = "link"
        label = _("Item")
        collapsed = True


class JoinBlock(ThemedBlock):
    items = blocks.ListBlock(JoinItemBlock())

    class Meta:
        icon = "link"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/join.html"
        form_layout = blocks.BlockGroup(
            children=["items"],
            settings=["design", "audience"],
        )


__all__ = [
    "AuraBlock",
    "CarouselBlock",
    "DrawerBlock",
    "FilterBlock",
    "JoinBlock",
    "DropdownBlock",
    "FabBlock",
    "IndicatorBlock",
    "MaskBlock",
    "PaginationBlock",
    "StackBlock",
    "SwapBlock",
    "TabItemBlock",
    "TabsBlock",
]
