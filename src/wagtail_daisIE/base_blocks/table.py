from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import (
    TABLE_BORDER_CHOICES,
    TABLE_SIZE_CHOICES,
)
from wagtail_daisIE.widgets import (
    DaisyUIIntegerBlock,
    DaisyUINumberSliderWidget,
    DaisyUISliderWidget,
)


class TableBorderSpacingBlock(blocks.StructBlock):
    all_spacing = DaisyUIIntegerBlock(
        default=None,
        required=False,
        max_value=96,
        label=_("All border spacing"),
        help_text=_(
            "Border spacing for all sides. Use the individual spacing fields for more control."
        ),
        widget=DaisyUINumberSliderWidget(min_value=0, max_value=96, step=1, suffix=""),
    )
    horizontal = DaisyUIIntegerBlock(
        default=None,
        required=False,
        max_value=96,
        label=_("Horizontal spacing"),
        widget=DaisyUINumberSliderWidget(min_value=0, max_value=96, step=1, suffix=""),
    )
    vertical = DaisyUIIntegerBlock(
        default=None,
        required=False,
        max_value=96,
        label=_("Vertical spacing"),
        widget=DaisyUINumberSliderWidget(min_value=0, max_value=96, step=1, suffix=""),
    )

    class Meta:
        icon = "expand-right"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "all_spacing",
                "horizontal",
                "vertical",
            ],
            heading=_("Spacing"),
        )


class TableAppearanceBlock(blocks.StructBlock):
    table_size = blocks.ChoiceBlock(
        choices=TABLE_SIZE_CHOICES,
        default="",
        required=False,
        label=_("Table size (width)"),
        widget=DaisyUISliderWidget(),
    )
    table_border_spacing = TableBorderSpacingBlock()
    table_border_style = blocks.ChoiceBlock(
        choices=TABLE_BORDER_CHOICES,
        default="",
        required=False,
        label=_("Table border style"),
    )
    table_zebra_rows = blocks.BooleanBlock(
        default=False,
        label=_("Zebra rows"),
        help_text=_("Alternate row background colors"),
    )
    table_pin_rows = blocks.BooleanBlock(
        default=False,
        label=_("Pin rows"),
        help_text=_("Rows in table headers and footers are always visible"),
    )
    table_pin_columns = blocks.BooleanBlock(
        default=False,
        label=_("Pin columns"),
        help_text=_("Columns in table headers and footers are always visible"),
    )

    class Meta:
        icon = "grid"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "table_size",
                "table_border_style",
                "table_border_spacing",
                "table_zebra_rows",
                "table_pin_rows",
                "table_pin_columns",
            ],
            heading=_("Table appearance"),
        )
