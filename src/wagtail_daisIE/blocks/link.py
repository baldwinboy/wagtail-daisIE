from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.base_blocks import (
    AbstractLinkBlock,
    LinkDestinationBlock,
    ThemedButtonBlock,
    ThemedTypographyBlock,
)
from wagtail_daisIE.icons.blocks import IconChooserBlock


class InlineLinkBlock(AbstractLinkBlock, ThemedTypographyBlock):
    destination = LinkDestinationBlock(min_num=1)
    text = blocks.CharBlock(
        max_length=255,
        blank=True,
        label=_("Text"),
    )

    class Meta:
        icon = "link"
        group = _("Inline Link")
        collapsed = True
        template = "wagtail_daisIE/blocks/link.html"
        form_layout = blocks.BlockGroup(
            children=["text", "destination", "open_in_new_tab"],
            settings=["design", "audience"],
        )


class LabelLinkBlock(AbstractLinkBlock, ThemedTypographyBlock):
    destination = LinkDestinationBlock(min_num=1)
    text = blocks.CharBlock(
        max_length=255,
        blank=True,
        label=_("Text"),
    )
    icon = IconChooserBlock(required=False)

    class Meta:
        icon = "link"
        group = _("Link with label")
        collapsed = True
        template = "wagtail_daisIE/blocks/link.html"
        form_layout = blocks.BlockGroup(
            children=["text", "icon", "destination", "open_in_new_tab"],
            settings=["design", "audience"],
        )


class ButtonBlock(AbstractLinkBlock, ThemedButtonBlock):
    text = blocks.CharBlock(
        max_length=255,
        blank=True,
        label=_("Text"),
    )
    icon = IconChooserBlock(required=False)

    class Meta:
        icon = "link"
        group = _("Button")
        collapsed = True
        template = "wagtail_daisIE/blocks/button.html"
        form_layout = blocks.BlockGroup(
            children=["text", "icon", "destination", "open_in_new_tab"],
            settings=["design", "audience"],
        )
