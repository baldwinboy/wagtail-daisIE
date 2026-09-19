from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from .base import (
    ThemedTypographyBlock,
)


class InlineTextBlock(ThemedTypographyBlock):
    text = blocks.CharBlock(
        max_length=255,
        help_text=_("Text content for the inline block."),
        blank=True,
    )

    def __init__(self, *args, **kwargs):
        max_length = kwargs.pop("max_length", None)
        super().__init__(*args, **kwargs)
        if isinstance(max_length, int) and "text" in self.child_blocks:
            self.child_blocks["text"].field.max_length = max_length

    class Meta:
        icon = "tag"
        group = _("Text")
        collapsed = True
        template = "wagtail_daisIE/blocks/inline_text.html"
        form_layout = blocks.BlockGroup(
            children=["text"],
            settings=["design", "audience"],
        )


class InlineRichTextBlock(ThemedTypographyBlock):
    text = blocks.RichTextBlock(
        help_text=_("Rich text content for the inline block."),
        blank=True,
    )

    class Meta:
        icon = "doc-full"
        group = _("Text")
        collapsed = True
        template = "wagtail_daisIE/blocks/inline_rich_text.html"
        form_layout = blocks.BlockGroup(
            children=["text"],
            settings=["design", "audience"],
        )


class HeaderBlock(InlineTextBlock):
    class Meta:
        icon = "title"
        group = _("Text")
        collapsed = True
        template = "wagtail_daisIE/blocks/header.html"


class CopyrightBlock(InlineTextBlock):
    text = blocks.CharBlock(
        max_length=512,
        help_text=_(
            "Copyright text. This will sit alongside the copyright symbol and "
            "current year, so should just be the name of the copyright holder."
        ),
        blank=True,
    )

    class Meta:
        icon = "date"
        group = _("Text")
        collapsed = True
        template = "wagtail_daisIE/blocks/copyright.html"
