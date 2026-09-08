from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import ALIGNMENT_CHOICES, JUSTIFY_CHOICES
from wagtail_daisIE.widgets import DaisyUIIntegerBlock, DaisyUINumberSliderWidget

from .spaced import SpacedBlockWithList


def _layout_form_layout(children, extra_settings):
    return blocks.BlockGroup(
        children=children,
        settings=["design", "alignment", "audience", *extra_settings],
    )


class RowBlock(SpacedBlockWithList):
    horizontal_alignment = blocks.ChoiceBlock(
        choices=JUSTIFY_CHOICES,
        default="",
        required=False,
        help_text=_("Horizontal alignment of items within the row."),
    )
    vertical_alignment = blocks.ChoiceBlock(
        choices=ALIGNMENT_CHOICES,
        default="",
        required=False,
        help_text=_("Vertical alignment of items within the row."),
    )

    class Meta:
        icon = "expand-right"
        group = _("Row")
        collapsed = True
        template = "wagtail_daisIE/blocks/row.html"
        form_layout = _layout_form_layout(
            ["content"],
            ["horizontal_alignment", "vertical_alignment"],
        )


class ColumnBlock(SpacedBlockWithList):
    horizontal_alignment = blocks.ChoiceBlock(
        choices=ALIGNMENT_CHOICES,
        default="",
        required=False,
        help_text=_("Horizontal alignment of items within the column."),
    )
    vertical_alignment = blocks.ChoiceBlock(
        choices=JUSTIFY_CHOICES,
        default="",
        required=False,
        help_text=_("Vertical alignment of items within the column."),
    )

    class Meta:
        icon = "collapse-down"
        group = _("Column")
        collapsed = True
        template = "wagtail_daisIE/blocks/column.html"
        form_layout = _layout_form_layout(
            ["content"],
            ["horizontal_alignment", "vertical_alignment"],
        )


class GridBlock(SpacedBlockWithList):
    horizontal_alignment = blocks.ChoiceBlock(
        choices=JUSTIFY_CHOICES,
        default="",
        required=False,
        help_text=_("Horizontal alignment of items within the grid."),
    )
    vertical_alignment = blocks.ChoiceBlock(
        choices=ALIGNMENT_CHOICES,
        default="",
        required=False,
        help_text=_("Vertical alignment of items within the grid."),
    )
    num_columns = DaisyUIIntegerBlock(
        default=2,
        min_value=1,
        max_value=6,
        help_text=_("Number of columns in the grid."),
        widget=DaisyUINumberSliderWidget(min_value=1, max_value=6, step=1),
    )
    gap = blocks.ChoiceBlock(
        choices=[
            ("gap-1", "1"),
            ("gap-2", "2"),
            ("gap-3", "3"),
            ("gap-4", "4"),
            ("gap-6", "6"),
            ("gap-8", "8"),
        ],
        default="gap-4",
        required=False,
        label=_("Grid gap"),
    )

    class Meta:
        icon = "table"
        group = _("Grid")
        collapsed = True
        template = "wagtail_daisIE/blocks/grid.html"
        form_layout = _layout_form_layout(
            ["num_columns", "gap", "content"],
            ["horizontal_alignment", "vertical_alignment"],
        )
