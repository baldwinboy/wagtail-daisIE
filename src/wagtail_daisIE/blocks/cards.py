from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from .base import ThemedBlock
from .inline import HeaderBlock, InlineRichTextBlock, InlineTextBlock
from .link import ButtonBlock, InlineLinkBlock
from .media import EmbedBlock, ImageBlock
from .section import SectionBlock


BASE_CONTENT_BLOCKS = [
    ("image", ImageBlock()),
    ("header", HeaderBlock()),
    ("text", InlineTextBlock()),
    ("rich_text", InlineRichTextBlock()),
    ("button", ButtonBlock()),
    ("inline_link", InlineLinkBlock()),
    ("embed", EmbedBlock()),
]

INLINE_CARD_CONTENT = [
    ("text", InlineTextBlock()),
    ("rich_text", InlineRichTextBlock()),
    ("header", HeaderBlock()),
    ("image", ImageBlock()),
    ("button", ButtonBlock()),
    ("inline_link", InlineLinkBlock()),
    ("embed", EmbedBlock()),
]


class InlineCardBlock(ThemedBlock):
    content = blocks.StreamBlock(
        INLINE_CARD_CONTENT,
        label=_("Card content"),
    )

    class Meta:
        icon = "minus"
        group = _("Cards")
        collapsed = True
        template = "wagtail_daisIE/blocks/card.html"
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "audience"],
        )


INLINE_CONTENT_BLOCKS = [
    *BASE_CONTENT_BLOCKS,
    ("inline_card", InlineCardBlock()),
]

CARD_CONTENT_BLOCKS = [
    *INLINE_CONTENT_BLOCKS,
]


class CardBlock(SectionBlock):
    content = blocks.StreamBlock(
        CARD_CONTENT_BLOCKS,
        label=_("Card content"),
    )

    class Meta:
        icon = "bars"
        group = _("Cards")
        collapsed = True
        template = "wagtail_daisIE/blocks/card.html"
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "alignment", "audience"],
        )


CONTENT_BLOCKS = [
    *INLINE_CONTENT_BLOCKS,
    ("card", CardBlock()),
]
