from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.contrib.table_block.blocks import TableBlock as WagtailTableBlock

from ..base_blocks import ThemedTableBlock


class TableContentBlock(WagtailTableBlock):
    class Meta:
        template = "wagtail_daisIE/blocks/table_content.html"


class TableBlock(ThemedTableBlock):
    content = TableContentBlock()

    class Meta:
        icon = "table"
        group = _("Table")
        template = "wagtail_daisIE/blocks/table.html"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "cell_design", "header_cell_design", "audience"],
        )
