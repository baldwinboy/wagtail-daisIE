from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.base_blocks import (
    AbstractLinkBlock,
    InlineMarkupBlock,
    LinkDestinationBlock,
    ThemedButtonBlock,
    ThemedTypographyBlock,
)
from wagtail_daisIE.icons.blocks import IconChooserBlock


class InlineLinkBlock(AbstractLinkBlock, ThemedTypographyBlock):
    destination = LinkDestinationBlock(min_num=1)
    text = InlineMarkupBlock(
        max_length=255,
        required=False,
    )

    class Meta:
        icon = "link"
        group = _("Link")
        collapsed = True
        template = "wagtail_daisIE/blocks/link.html"
        form_layout = blocks.BlockGroup(
            children=["text", "destination", "open_in_new_tab"],
            settings=["design", "audience"],
        )


class LabelLinkBlock(AbstractLinkBlock, ThemedTypographyBlock):
    destination = LinkDestinationBlock(min_num=1)
    text = InlineMarkupBlock(
        max_length=255,
        required=False,
    )
    icon = IconChooserBlock(required=False)
    icon_after = blocks.BooleanBlock(
        default=True,
        required=False,
        help_text=_("Place the icon after the text"),
    )

    class Meta:
        icon = "link"
        group = _("Link")
        collapsed = True
        template = "wagtail_daisIE/blocks/link.html"
        form_layout = blocks.BlockGroup(
            children=["text", "icon", "icon_after", "destination", "open_in_new_tab"],
            settings=["design", "audience"],
        )


class ButtonBlock(AbstractLinkBlock, ThemedButtonBlock):
    text = InlineMarkupBlock(
        max_length=255,
        required=False,
    )
    icon = IconChooserBlock(required=False)
    icon_after = blocks.BooleanBlock(
        default=True,
        required=False,
        help_text=_("Place the icon after the text"),
    )
    make_parent_clickable = blocks.BooleanBlock(
        default=False,
        required=False,
        label=_("Make the parent card clickable"),
        help_text=_(
            "Only applies inside a card: the button stretches to cover the "
            "whole card so it can be clicked anywhere. Ignored elsewhere."
        ),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        # The stretch behaviour is only valid inside a card; the card marks its
        # content with ``card_clickable_container``.
        container = bool((parent_context or {}).get("card_clickable_container"))
        context["stretch_to_parent"] = container and bool(
            value.get("make_parent_clickable")
        )
        return context

    class Meta:
        icon = "link"
        group = _("Link")
        collapsed = True
        template = "wagtail_daisIE/blocks/button.html"
        form_layout = blocks.BlockGroup(
            children=[
                "text",
                "icon",
                "icon_after",
                "destination",
                "open_in_new_tab",
                "make_parent_clickable",
            ],
            settings=["design", "audience"],
        )
