"""Layout/decorative component blocks (stack, aura, mask, dropdown, swap)."""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.images.blocks import ImageBlock as WagtailImageBlock

from ..base_blocks import (
    ButtonAppearanceBlock,
    DesignBlock,
    InlineMarkupBlock,
    ThemedBlock,
    collapsed_group,
)
from ..base_blocks.audience import AudienceBlock, evaluate_audience
from ..base_blocks.compact import DaisieStructBlock
from ..base_blocks.css import build_design_css
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
from .spaced import SpacedBlock
from .stream import (
    DrawerSideStreamBlock,
    DropdownItemsStreamBlock,
    InlineStreamBlock,
    SlideContentStreamBlock,
    TabContentStreamBlock,
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
        icon = "bars"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/stack.html"
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "audience"],
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
            settings=["design", "audience"],
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
        icon = "radio-full"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/indicator.html"
        form_layout = blocks.BlockGroup(
            children=["item", "color", "position", "content"],
            settings=["design", "alignment", "audience"],
        )


class IndicatorInlineBlock(IndicatorBlock):
    content = InlineStreamBlock()

    class Meta:
        label = _("Indicator (inline)")


class StackInlineBlock(StackBlock):
    content = InlineStreamBlock()

    class Meta:
        label = _("Stack (inline)")


class AuraInlineBlock(AuraBlock):
    content = InlineStreamBlock()

    class Meta:
        label = _("Aura (inline)")


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
    content = DropdownItemsStreamBlock()

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
        icon = "resubmit"
        group = _("Actions")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/swap.html"
        form_layout = blocks.BlockGroup(
            children=["on_text", "off_text", "effect"],
            settings=["design", "audience"],
        )


class TabItemBlock(DaisieStructBlock):
    label = blocks.CharBlock(max_length=128)
    key = blocks.CharBlock(
        max_length=64,
        required=False,
        blank=True,
        label=_("Key"),
        help_text=_("Optional stable id used by ?tab= links."),
    )
    icon = IconChooserBlock(required=False)
    audience = AudienceBlock()
    content = TabContentStreamBlock()

    class Meta:
        icon = "doc-full"
        label = _("Tab")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "label",
                "key",
                collapsed_group(_("Icon"), "icon", icon="image"),
                "content",
            ],
            settings=["audience"],
        )


class TabItemInlineBlock(TabItemBlock):
    content = InlineStreamBlock()

    class Meta:
        label = _("Tab (inline)")


class TabsBlock(ThemedBlock):
    tabs = blocks.ListBlock(TabItemBlock())
    style = blocks.ChoiceBlock(choices=TABS_STYLE_CHOICES, default="tabs-box")
    size = blocks.ChoiceBlock(choices=TABS_SIZE_CHOICES, default="", required=False)
    placement = blocks.ChoiceBlock(
        choices=TABS_PLACEMENT_CHOICES, default="", required=False
    )
    panel_design = DesignBlock()

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        request = (parent_context or {}).get("request")
        requested = (
            (getattr(request, "GET", None) or {}).get("tab") if request else None
        )
        tabs = []
        for index, tab in enumerate((value or {}).get("tabs") or []):
            selected = (tab.get("audience") or {}).get("audience") or []
            key = str(tab.get("key") or index)
            tabs.append(
                {
                    "label": tab.get("label"),
                    "icon": tab.get("icon"),
                    "content": tab.get("content"),
                    "key": key,
                    "allowed": evaluate_audience(selected, request),
                    "checked": requested == key or (not requested and index == 0),
                }
            )
        if not any(tab["checked"] and tab["allowed"] for tab in tabs):
            for tab in tabs:
                if tab["allowed"]:
                    tab["checked"] = True
                    break
        context["tabs"] = tabs
        context["tab_panel_css"] = build_design_css(value.get("panel_design"))
        return context

    class Meta:
        icon = "list-ul"
        group = _("Navigation")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/tabs.html"
        form_layout = blocks.BlockGroup(
            children=["tabs", "style", "size", "placement"],
            settings=["design", "panel_design", "audience"],
        )


class TabsInlineBlock(TabsBlock):
    tabs = blocks.ListBlock(TabItemInlineBlock())

    class Meta:
        label = _("Tabs (inline)")


class CarouselSlideBlock(DaisieStructBlock):
    image = WagtailImageBlock()
    caption = blocks.CharBlock(max_length=255, required=False, blank=True)
    content = SlideContentStreamBlock()

    class Meta:
        icon = "image"
        label = _("Slide")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=["image", "caption", "content"],
        )


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


class PaginationItemBlock(DaisieStructBlock):
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


class FabItemBlock(DaisieStructBlock):
    label = blocks.CharBlock(max_length=64)
    icon = IconChooserBlock(required=False)
    destination = LinkDestinationBlock()

    class Meta:
        icon = "link"
        label = _("Action")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "label",
                "destination",
                collapsed_group(_("Icon"), "icon", icon="image"),
            ],
        )


class FabBlock(ThemedBlock):
    trigger_icon = IconChooserBlock(required=False)
    trigger_label = blocks.CharBlock(max_length=64, required=False, blank=True)
    trigger_appearance = ButtonAppearanceBlock(required=False)
    items = blocks.ListBlock(FabItemBlock(), label=_("Actions"))

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
        context["fab_trigger_css"] = build_design_css(
            {"button_appearance": value.get("trigger_appearance")}
        )
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
            children=[
                collapsed_group(_("Trigger icon"), "trigger_icon", icon="image"),
                "trigger_label",
                "items",
            ],
            settings=["design", "trigger_appearance", "audience"],
        )


class HeroBlock(SpacedBlock):
    overlay = blocks.BooleanBlock(default=False, required=False)
    full_width = blocks.BooleanBlock(
        default=True,
        required=False,
        help_text=_("Break out of the page container to span the viewport."),
    )

    class Meta:
        abstract = False
        icon = "image"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/hero.html"
        form_layout = blocks.BlockGroup(
            children=["overlay", "full_width", "content"],
            settings=["design", "alignment", "audience"],
        )


class HeroInlineBlock(HeroBlock):
    content = InlineStreamBlock()

    class Meta:
        label = _("Hero (inline)")


class DrawerBlock(SpacedBlock):
    side = DrawerSideStreamBlock()

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


class DrawerInlineBlock(DrawerBlock):
    side = InlineStreamBlock()
    content = InlineStreamBlock()

    class Meta:
        label = _("Drawer (inline)")


class FilterBlock(ThemedBlock):
    name = blocks.CharBlock(
        max_length=64, required=False, blank=True, label=_("Group name")
    )
    options = blocks.ListBlock(blocks.CharBlock(max_length=64, label=_("Option")))

    class Meta:
        icon = "sliders"
        group = _("Data input")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout/filter.html"
        form_layout = blocks.BlockGroup(
            children=["name", "options"],
            settings=["design", "audience"],
        )


class JoinItemBlock(DaisieStructBlock):
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
