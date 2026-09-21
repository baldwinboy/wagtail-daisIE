"""The page content blocks, shared by page bodies and data components.

Kept free of the data-driven blocks (``feed``/``calendar``/``action``) so that a
feed's item cards can reuse every page block without recursion and without an
import cycle.
"""

from ..notifications.blocks import NewsletterSignupBlock
from .accordion import AccordionBlock
from .blockquote import BlockQuote
from .cards import CARD_CONTENT_BLOCKS, CONTENT_BLOCKS, INLINE_CARD_CONTENT
from .feedback import FEEDBACK_BLOCKS
from .inline import CopyrightBlock
from .inputs import INPUT_BLOCKS
from .layout import ColumnBlock, GridBlock, RowBlock
from .marquee import MarqueeBlock
from .spaced import LIST_CONTENT_BLOCKS
from .table import TableBlock


PAGE_CONTENT_BLOCKS = [
    *LIST_CONTENT_BLOCKS,
    ("accordion", AccordionBlock()),
    ("row", RowBlock()),
    ("column", ColumnBlock()),
    ("grid", GridBlock()),
    ("table", TableBlock()),
    ("marquee", MarqueeBlock()),
    ("copyright", CopyrightBlock()),
    ("blockquote", BlockQuote()),
    ("newsletter", NewsletterSignupBlock()),
    *FEEDBACK_BLOCKS,
    *INPUT_BLOCKS,
]


__all__ = [
    "CARD_CONTENT_BLOCKS",
    "CONTENT_BLOCKS",
    "INLINE_CARD_CONTENT",
    "PAGE_CONTENT_BLOCKS",
]
