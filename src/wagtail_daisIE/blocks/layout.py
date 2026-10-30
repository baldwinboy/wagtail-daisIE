from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.base_blocks.audience import AudienceBlock, evaluate_audience
from wagtail_daisIE.base_blocks.compact import DaisieStructBlock
from wagtail_daisIE.base_blocks.css import build_layout_item_css
from wagtail_daisIE.base_blocks.layout_design import LayoutItemDesignBlock
from wagtail_daisIE.choices import (
    FLEX_WRAP_CHOICES,
)
from wagtail_daisIE.widgets import DaisyUIIntegerBlock, DaisyUINumberSliderWidget

from .spaced import SpacedBlockWithList
from .stream import (
    ColumnContentStreamBlock,
    GridContentStreamBlock,
    InlineColumnContentStreamBlock,
    InlineGridContentStreamBlock,
    InlineRowContentStreamBlock,
    InlineStreamBlock,
    LayoutStreamBlock,
    RowContentStreamBlock,
)


def _layout_form_layout(children, extra_settings):
    return blocks.BlockGroup(
        children=children,
        settings=["design", "alignment", *extra_settings, "audience"],
    )


class LayoutItemBlock(DaisieStructBlock):
    content = LayoutStreamBlock()
    design = LayoutItemDesignBlock()
    audience = AudienceBlock()

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        block_value = value or {}
        block_parent_context = parent_context or {}
        context["layout_item_css"] = build_layout_item_css(
            block_value.get("design"),
            grid=bool(block_parent_context.get("layout_item_grid")),
        )
        audience_keys = block_value.get("audience") or []
        request = block_parent_context.get("request")
        context["audience_allowed"] = evaluate_audience(audience_keys, request)
        return context

    class Meta:
        icon = "expand-right"
        group = _("Layout")
        label = _("Layout item")
        collapsed = True
        template = "wagtail_daisIE/blocks/layout_item.html"
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "audience"],
            heading=_("Layout item"),
            help_text=_(
                "Empty fields inherit the container's default layout. "
                "Grid spans only apply inside a grid."
            ),
        )


class InlineLayoutItemBlock(LayoutItemBlock):
    content = InlineStreamBlock()

    class Meta:
        label = _("Layout item (inline)")


class RowBlock(SpacedBlockWithList):
    content = RowContentStreamBlock()
    wrap = blocks.ChoiceBlock(
        choices=FLEX_WRAP_CHOICES,
        default="flex-wrap",
        required=False,
        label=_("Wrap"),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        scroll = (((value or {}).get("design") or {}).get("size") or {}).get(
            "scroll", ""
        )
        horizontal = scroll in {"overflow-x-auto", "overflow-auto"}
        context["row_wrap_css"] = (
            "" if horizontal else ((value or {}).get("wrap") or "flex-wrap")
        )
        context["row_scroll_css"] = "flex-nowrap" if horizontal else ""
        context["layout_item_grid"] = False
        return context

    class Meta:
        icon = "expand-right"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/row.html"
        form_layout = _layout_form_layout(
            ["content"],
            ["wrap"],
        )


class ColumnBlock(SpacedBlockWithList):
    content = ColumnContentStreamBlock()

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["layout_item_grid"] = False
        return context

    class Meta:
        icon = "collapse-down"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/column.html"
        form_layout = _layout_form_layout(
            ["content"],
            [],
        )


class RowInlineBlock(RowBlock):
    content = InlineRowContentStreamBlock()

    class Meta:
        label = _("Row (inline)")


class ColumnInlineBlock(ColumnBlock):
    content = InlineColumnContentStreamBlock()

    class Meta:
        label = _("Column (inline)")


class GridBlock(SpacedBlockWithList):
    content = GridContentStreamBlock()
    num_columns = DaisyUIIntegerBlock(
        default=2,
        min_value=1,
        max_value=6,
        help_text=_("Number of columns in the grid."),
        widget=DaisyUINumberSliderWidget(min_value=1, max_value=6, step=1),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["layout_item_grid"] = True
        return context

    class Meta:
        icon = "table"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/grid.html"
        form_layout = _layout_form_layout(
            ["num_columns", "content"],
            [],
        )


class GridInlineBlock(GridBlock):
    content = InlineGridContentStreamBlock()

    class Meta:
        label = _("Grid (inline)")
