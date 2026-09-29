"""The page content blocks, shared by page bodies and data components.

Kept free of the data-driven blocks (``feed``/``calendar``/``action``) so that a
feed's item cards can reuse every page block without recursion and without an
import cycle.
"""

from django.conf import settings

from .accordion import AccordionBlock
from .blockquote import BlockQuote
from .breadcrumbs import BreadcrumbsBlock
from .cards import CARD_CONTENT_BLOCKS, CONTENT_BLOCKS, INLINE_CARD_CONTENT
from .display import (
    AvatarBlock,
    BadgeBlock,
    ChatBlock,
    CountdownBlock,
    DiffBlock,
    DividerBlock,
    Hover3DCardBlock,
    HoverGalleryBlock,
    KbdBlock,
    SkeletonBlock,
    StatBlock,
    TextRotateBlock,
    TimelineBlock,
)
from .feedback import FEEDBACK_BLOCKS
from .inline import CopyrightBlock
from .inputs import INPUT_BLOCKS
from .layout import ColumnBlock, GridBlock, RowBlock
from .layout_components import (
    AuraBlock,
    CarouselBlock,
    DrawerBlock,
    DropdownBlock,
    FabBlock,
    FilterBlock,
    HeroBlock,
    IndicatorBlock,
    JoinBlock,
    MaskBlock,
    PaginationBlock,
    StackBlock,
    SwapBlock,
    TabsBlock,
)
from .marquee import MarqueeBlock
from .mockups import (
    MockupBrowserBlock,
    MockupCodeBlock,
    MockupPhoneBlock,
    MockupWindowBlock,
)
from .registry import content_block_contributions, register_content_block
from .spaced import LIST_CONTENT_BLOCKS
from .table import TableBlock


PAGE_CONTENT_BLOCKS = [
    ("breadcrumbs", BreadcrumbsBlock()),
    *LIST_CONTENT_BLOCKS,
    ("accordion", AccordionBlock()),
    ("row", RowBlock()),
    ("column", ColumnBlock()),
    ("grid", GridBlock()),
    ("table", TableBlock()),
    ("marquee", MarqueeBlock()),
    ("copyright", CopyrightBlock()),
    ("blockquote", BlockQuote()),
    ("badge", BadgeBlock()),
    ("kbd", KbdBlock()),
    ("divider", DividerBlock()),
    ("avatar", AvatarBlock()),
    ("stat", StatBlock()),
    ("countdown", CountdownBlock()),
    ("skeleton", SkeletonBlock()),
    ("text_rotate", TextRotateBlock()),
    ("chat", ChatBlock()),
    ("timeline", TimelineBlock()),
    ("diff", DiffBlock()),
    ("hover_gallery", HoverGalleryBlock()),
    ("hover_3d", Hover3DCardBlock()),
    ("stack", StackBlock()),
    ("aura", AuraBlock()),
    ("indicator", IndicatorBlock()),
    ("mask", MaskBlock()),
    ("dropdown", DropdownBlock()),
    ("swap", SwapBlock()),
    ("tabs", TabsBlock()),
    ("carousel", CarouselBlock()),
    ("pagination", PaginationBlock()),
    ("fab", FabBlock()),
    ("drawer", DrawerBlock()),
    ("hero", HeroBlock()),
    ("filter", FilterBlock()),
    ("join", JoinBlock()),
    ("mockup_browser", MockupBrowserBlock()),
    ("mockup_window", MockupWindowBlock()),
    ("mockup_phone", MockupPhoneBlock()),
    ("mockup_code", MockupCodeBlock()),
    *FEEDBACK_BLOCKS,
    *INPUT_BLOCKS,
]

if "wagtail_daisIE.notifications" in settings.INSTALLED_APPS:
    from ..notifications.blocks import NewsletterSignupBlock

    register_content_block("newsletter", NewsletterSignupBlock())

PAGE_CONTENT_BLOCKS.extend(content_block_contributions())


__all__ = [
    "BreadcrumbsBlock",
    "CARD_CONTENT_BLOCKS",
    "CONTENT_BLOCKS",
    "INLINE_CARD_CONTENT",
    "PAGE_CONTENT_BLOCKS",
]
