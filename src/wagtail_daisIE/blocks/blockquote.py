from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from .base import ThemedBlock


class BlockQuote(ThemedBlock):
    text = blocks.TextBlock(
        help_text=_("Quote text content."),
    )
    attribute_name = blocks.CharBlock(
        blank=True,
        required=False,
        help_text=_("Attribution name, e.g. 'Mary Berry'."),
        label=_("Attribution"),
    )

    class Meta:
        icon = "openquote"
        group = _("Text")
        collapsed = True
        template = "wagtail_daisIE/blocks/blockquote.html"
        form_layout = blocks.BlockGroup(
            children=["text", "attribute_name"],
            settings=["design", "audience"],
        )
