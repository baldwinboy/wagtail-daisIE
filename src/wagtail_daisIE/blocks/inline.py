from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import FONT_WEIGHT_CHOICES

from ..base_blocks import InlineMarkupBlock
from .base import (
    ThemedTypographyBlock,
)


_RETAINED_FONT_CLASSES = frozenset(
    [
        *(value for value, _label in FONT_WEIGHT_CHOICES if value),
        "font-sans",
        "font-serif",
        "font-mono",
    ]
)


class InlineTextBlock(ThemedTypographyBlock):
    text = InlineMarkupBlock(
        max_length=255,
        help_text=_("Text content for the inline block."),
        required=False,
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
        required=False,
    )

    def get_context(self, value, parent_context=None):
        parent_context = dict(parent_context or {})
        inherited = parent_context.get("text_css", "")
        if inherited:
            parent_context["text_css"] = " ".join(
                token
                for token in inherited.split()
                if not token.startswith("font-") or token in _RETAINED_FONT_CLASSES
            )
        return super().get_context(value, parent_context)

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
    text = InlineMarkupBlock(
        max_length=512,
        help_text=_(
            "Copyright text. This will sit alongside the copyright symbol and "
            "current year, so should just be the name of the copyright holder."
        ),
        required=False,
    )

    class Meta:
        icon = "date"
        group = _("Text")
        collapsed = True
        template = "wagtail_daisIE/blocks/copyright.html"
