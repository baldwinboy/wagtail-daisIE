from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import (
    FLEX_WRAP_CHOICES,
)
from wagtail_daisIE.widgets import DaisyUIIntegerBlock, DaisyUINumberSliderWidget

from .spaced import SpacedBlockWithList


def _layout_form_layout(children, extra_settings):
    return blocks.BlockGroup(
        children=children,
        settings=["design", "alignment", *extra_settings, "audience"],
    )


class RowBlock(SpacedBlockWithList):
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
        context["row_item_css"] = "shrink-0" if horizontal else "flex-1 min-w-0"
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
    class Meta:
        icon = "collapse-down"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/column.html"
        form_layout = _layout_form_layout(
            ["content"],
            [],
        )


class GridBlock(SpacedBlockWithList):
    num_columns = DaisyUIIntegerBlock(
        default=2,
        min_value=1,
        max_value=6,
        help_text=_("Number of columns in the grid."),
        widget=DaisyUINumberSliderWidget(min_value=1, max_value=6, step=1),
    )

    class Meta:
        icon = "table"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/grid.html"
        form_layout = _layout_form_layout(
            ["num_columns", "content"],
            [],
        )
