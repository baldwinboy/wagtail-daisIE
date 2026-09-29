from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..dynamic.action_blocks import ActionBlock
from .base import ThemedBlock
from .inline import HeaderBlock, InlineRichTextBlock, InlineTextBlock
from .link import ButtonBlock, InlineLinkBlock
from .media import EmbedBlock, ImageBlock
from .section import SectionBlock


def _card_is_clickable(content):
    """Return whether the card content contains a click-to-stretch control.

    Both a plain button and an action button expose ``make_parent_clickable``;
    when set, the control renders as a bare overlay covering the card. Only the
    card marks its content as a clickable container, so the flag is inert
    outside a card.
    """
    for child in content or []:
        block_type = getattr(child, "block_type", None)
        value = child.value if hasattr(child, "value") else child
        if not hasattr(value, "get"):
            continue
        if block_type == "button" and value.get("make_parent_clickable"):
            return True
        if block_type == "action":
            button = value.get("button") or {}
            if hasattr(button, "get") and button.get("make_parent_clickable"):
                return True
    return False


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
    ("action", ActionBlock()),
]


class InlineCardBlock(ThemedBlock):
    content = blocks.StreamBlock(
        INLINE_CARD_CONTENT,
        label=_("Card content"),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["card_clickable"] = _card_is_clickable((value or {}).get("content"))
        return context

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
    ("action", ActionBlock()),
]


class CardBlock(SectionBlock):
    content = blocks.StreamBlock(
        CARD_CONTENT_BLOCKS,
        label=_("Card content"),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["card_clickable"] = _card_is_clickable((value or {}).get("content"))
        return context

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
