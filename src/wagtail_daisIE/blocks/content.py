from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..dynamic.blocks_data import DATA_BLOCKS
from .accordion import AccordionBlock
from .blockquote import BlockQuote
from .cards import CARD_CONTENT_BLOCKS, CONTENT_BLOCKS, INLINE_CARD_CONTENT
from .content_blocks import PAGE_CONTENT_BLOCKS
from .feedback import FEEDBACK_BLOCKS
from .inline import CopyrightBlock
from .inputs import INPUT_BLOCKS
from .layout import ColumnBlock, GridBlock, RowBlock
from .marquee import MarqueeBlock
from .section import SectionBlock
from .spaced import LIST_CONTENT_BLOCKS
from .table import TableBlock


ALL_CONTENT_BLOCKS = [
    *PAGE_CONTENT_BLOCKS,
    *DATA_BLOCKS,
]


class ContentBlock(blocks.StreamBlock):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("local_blocks", ALL_CONTENT_BLOCKS)
        super().__init__(*args, **kwargs)

    class Meta:
        icon = "plus-inverse"
        group = _("Content")
        collapsed = True
        template = "wagtail_daisIE/blocks/content.html"


CONTENT_BLOCK = ContentBlock


__all__ = [
    "AccordionBlock",
    "ALL_CONTENT_BLOCKS",
    "BlockQuote",
    "CARD_CONTENT_BLOCKS",
    "ColumnBlock",
    "CONTENT_BLOCKS",
    "CONTENT_BLOCK",
    "ContentBlock",
    "CopyrightBlock",
    "FEEDBACK_BLOCKS",
    "GridBlock",
    "INLINE_CARD_CONTENT",
    "INPUT_BLOCKS",
    "LIST_CONTENT_BLOCKS",
    "MarqueeBlock",
    "RowBlock",
    "SectionBlock",
    "TableBlock",
]
