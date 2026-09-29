"""daisyUI mockup blocks (browser, window, code, phone)."""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks import ThemedBlock
from .spaced import LIST_CONTENT_BLOCKS


class MockupBrowserBlock(ThemedBlock):
    url = blocks.CharBlock(
        max_length=255, required=False, blank=True, default="https://"
    )
    content = blocks.StreamBlock(LIST_CONTENT_BLOCKS)

    class Meta:
        icon = "browser"
        group = _("Mockups")
        collapsed = True
        template = "wagtail_daisIE/blocks/mockups/browser.html"
        form_layout = blocks.BlockGroup(
            children=["url", "content"],
            settings=["design", "audience"],
        )


class MockupWindowBlock(ThemedBlock):
    content = blocks.StreamBlock(LIST_CONTENT_BLOCKS)

    class Meta:
        icon = "placeholder"
        group = _("Mockups")
        collapsed = True
        template = "wagtail_daisIE/blocks/mockups/window.html"
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "audience"],
        )


class MockupPhoneBlock(ThemedBlock):
    content = blocks.StreamBlock(LIST_CONTENT_BLOCKS)

    class Meta:
        icon = "mobile-alt"
        group = _("Mockups")
        collapsed = True
        template = "wagtail_daisIE/blocks/mockups/phone.html"
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "audience"],
        )


class MockupCodeLineBlock(blocks.StructBlock):
    prefix = blocks.CharBlock(max_length=8, required=False, blank=True, default="$")
    code = blocks.CharBlock(max_length=500)

    class Meta:
        icon = "code"
        label = _("Line")
        collapsed = True


class MockupCodeBlock(ThemedBlock):
    lines = blocks.ListBlock(MockupCodeLineBlock())

    class Meta:
        icon = "code"
        group = _("Mockups")
        collapsed = True
        template = "wagtail_daisIE/blocks/mockups/code.html"
        form_layout = blocks.BlockGroup(
            children=["lines"],
            settings=["design", "audience"],
        )


__all__ = [
    "MockupBrowserBlock",
    "MockupCodeBlock",
    "MockupCodeLineBlock",
    "MockupPhoneBlock",
    "MockupWindowBlock",
]
