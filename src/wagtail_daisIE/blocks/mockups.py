"""daisyUI mockup blocks (browser, window, code, phone)."""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks import ThemedBlock
from ..base_blocks.compact import DaisieStructBlock
from .stream import InlineLayoutStreamBlock


class MockupBrowserBlock(ThemedBlock):
    url = blocks.CharBlock(
        max_length=255, required=False, blank=True, default="https://"
    )
    content = InlineLayoutStreamBlock()

    class Meta:
        icon = "desktop"
        group = _("Mockups")
        collapsed = True
        template = "wagtail_daisIE/blocks/mockups/browser.html"
        form_layout = blocks.BlockGroup(
            children=["url", "content"],
            settings=["design", "audience"],
        )


class MockupWindowBlock(ThemedBlock):
    content = InlineLayoutStreamBlock()

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
    content = InlineLayoutStreamBlock()

    class Meta:
        icon = "mobile-alt"
        group = _("Mockups")
        collapsed = True
        template = "wagtail_daisIE/blocks/mockups/phone.html"
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "audience"],
        )


class MockupCodeLineBlock(DaisieStructBlock):
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
