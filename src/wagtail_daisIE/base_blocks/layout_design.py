"""Reusable flex/grid layout controls.

``LayoutBlock`` is a compact design primitive that emits utility classes through
the standard :func:`build_design_css` pipeline, so any component can attach it
without restructuring its stored value. It covers row/column, wrapping row and
column, and a fixed grid with 1-6 responsive columns.
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import (
    ALIGNMENT_CHOICES,
    FLEX_WRAP_CHOICES,
    GAP_CHOICES,
    GRID_COLUMN_CHOICES,
    JUSTIFY_CHOICES,
    LAYOUT_ITEM_BASIS_CHOICES,
    LAYOUT_ITEM_GRID_COLUMN_SPAN_CHOICES,
    LAYOUT_ITEM_GRID_ROW_SPAN_CHOICES,
    LAYOUT_ITEM_GROW_CHOICES,
    LAYOUT_ITEM_JUSTIFY_SELF_CHOICES,
    LAYOUT_ITEM_ORDER_CHOICES,
    LAYOUT_ITEM_SELF_ALIGN_CHOICES,
    LAYOUT_ITEM_SHRINK_CHOICES,
    LAYOUT_ITEM_WIDTH_CHOICES,
    MAIN_LAYOUT_CHOICES,
)

from .box import MarginBlock
from .compact import DaisieStructBlock
from .css import build_design_css
from .responsive import responsive_overrides


class LayoutBlock(DaisieStructBlock):
    layout = blocks.ChoiceBlock(
        choices=MAIN_LAYOUT_CHOICES,
        default="",
        required=False,
        label=_("Layout"),
    )
    columns = blocks.ChoiceBlock(
        choices=GRID_COLUMN_CHOICES,
        required=False,
        label=_("Columns"),
        help_text=_("Used when the layout is a grid."),
    )
    wrap = blocks.ChoiceBlock(
        choices=FLEX_WRAP_CHOICES, required=False, label=_("Wrap")
    )
    justify = blocks.ChoiceBlock(
        choices=JUSTIFY_CHOICES, required=False, label=_("Justify")
    )
    align = blocks.ChoiceBlock(
        choices=ALIGNMENT_CHOICES, required=False, label=_("Align")
    )
    gap = blocks.ChoiceBlock(choices=GAP_CHOICES["ALL"], required=False, label=_("Gap"))
    responsive = responsive_overrides()

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["block_css"] = build_design_css(value)
        return context

    class Meta:
        icon = "bars"
        label = _("Layout")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "layout",
                "columns",
                "wrap",
                "justify",
                "align",
                "gap",
                "responsive",
            ],
            heading=_("Layout"),
        )


class LayoutItemDesignBlock(DaisieStructBlock):
    grow = blocks.ChoiceBlock(
        choices=LAYOUT_ITEM_GROW_CHOICES,
        default="",
        required=False,
        label=_("Grow"),
    )
    shrink = blocks.ChoiceBlock(
        choices=LAYOUT_ITEM_SHRINK_CHOICES,
        default="",
        required=False,
        label=_("Shrink"),
    )
    basis = blocks.ChoiceBlock(
        choices=LAYOUT_ITEM_BASIS_CHOICES,
        default="",
        required=False,
        label=_("Basis"),
    )
    width = blocks.ChoiceBlock(
        choices=LAYOUT_ITEM_WIDTH_CHOICES,
        default="",
        required=False,
        label=_("Width"),
    )
    margin = MarginBlock()
    order = blocks.ChoiceBlock(
        choices=LAYOUT_ITEM_ORDER_CHOICES,
        default="",
        required=False,
        label=_("Order"),
    )
    align_self = blocks.ChoiceBlock(
        choices=LAYOUT_ITEM_SELF_ALIGN_CHOICES,
        default="",
        required=False,
        label=_("Align self"),
    )
    grid_column_span = blocks.ChoiceBlock(
        choices=LAYOUT_ITEM_GRID_COLUMN_SPAN_CHOICES,
        default="",
        required=False,
        label=_("Column span"),
        help_text=_("Only applies when the layout item is inside a grid."),
    )
    grid_row_span = blocks.ChoiceBlock(
        choices=LAYOUT_ITEM_GRID_ROW_SPAN_CHOICES,
        default="",
        required=False,
        label=_("Row span"),
        help_text=_("Only applies when the layout item is inside a grid."),
    )
    justify_self = blocks.ChoiceBlock(
        choices=LAYOUT_ITEM_JUSTIFY_SELF_CHOICES,
        default="",
        required=False,
        label=_("Justify self"),
        help_text=_("Only applies when the layout item is inside a grid."),
    )

    class Meta:
        icon = "sliders"
        label = _("Layout item design")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "grow",
                "shrink",
                "basis",
                "width",
                "order",
                "align_self",
                "margin",
                blocks.BlockGroup(
                    children=[
                        "grid_column_span",
                        "grid_row_span",
                        "justify_self",
                    ],
                    heading=_("Grid item"),
                ),
            ],
            heading=_("Layout item"),
        )
