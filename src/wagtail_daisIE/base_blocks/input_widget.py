"""Editor design vocabulary for file/attachment input widgets.

``TrayDesignBlock`` styles the container that holds uploaded items;
``ItemDesignBlock`` styles a single item (token/card/avatar). Both are compact
blocks, so adding them to a block's design does not change its migration
representation. The ``render``/``fallback`` choices below drive which markup a
dynamic item clones and what shows when there is nothing to display.
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choicelist import ChoiceList
from wagtail_daisIE.choices import (
    ALIGNMENT_CHOICES,
    AVATAR_SHAPE_CHOICES,
    FLEX_WRAP_CHOICES,
    GAP_CHOICES,
    JUSTIFY_CHOICES,
    MAIN_LAYOUT_CHOICES,
)

from .design import SpacedDesignBlock, TypographyDesignBlock


#: The presentation of a file-input block.
UPLOAD_DISPLAY_CHOICES = ChoiceList(
    [
        ("default", _("Plain file input")),
        ("image", _("Single image (click to change)")),
        ("attachments", _("Attachment tray")),
    ],
    "UPLOAD_DISPLAY_CHOICES",
)

#: How each item in a tray is rendered.
RENDER_CHOICES = ChoiceList(
    [
        ("thumbnail", _("Thumbnail (icon for non-images)")),
        ("icon", _("File icon")),
        ("avatar", _("Avatar")),
    ],
    "RENDER_CHOICES",
)

#: What to show when an item has no preview (for example an empty avatar).
FALLBACK_CHOICES = ChoiceList(
    [
        ("icon", _("File icon")),
        ("initials", _("Initials")),
        ("placeholder", _("Placeholder")),
        ("none", _("Blank")),
    ],
    "FALLBACK_CHOICES",
)


class TrayDesignBlock(SpacedDesignBlock):
    layout = blocks.ChoiceBlock(
        choices=MAIN_LAYOUT_CHOICES,
        default="row",
        required=False,
        label=_("Layout"),
    )
    wrap = blocks.ChoiceBlock(
        choices=FLEX_WRAP_CHOICES, required=False, label=_("Wrap")
    )
    justify = blocks.ChoiceBlock(choices=JUSTIFY_CHOICES, required=False)
    align = blocks.ChoiceBlock(choices=ALIGNMENT_CHOICES, required=False)
    gap = blocks.ChoiceBlock(choices=GAP_CHOICES["ALL"], required=False)

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "layout",
                "wrap",
                "justify",
                "align",
                "gap",
                "size",
                "spacing",
                "background",
                "border",
                "padding",
                "margin",
                "box",
            ],
            heading=_("Tray design"),
        )


class ItemDesignBlock(TypographyDesignBlock):
    shape = blocks.ChoiceBlock(
        choices=AVATAR_SHAPE_CHOICES,
        required=False,
        label=_("Shape"),
    )

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "typography",
                "shape",
                "size",
                "background",
                "border",
                "padding",
                "margin",
                "box",
            ],
            heading=_("Item design"),
        )


class InputWidgetDesignBlock(TypographyDesignBlock):
    """Editor design for a file/attachment form field.

    The typography/size/box groups style the input element (as before); the
    nested ``tray``/``item`` blocks style the attachment tray and each item, and
    ``render``/``fallback`` choose the item markup. A frozen migration key keeps
    future edits from disturbing `DaisieFormField.input_design` migrations.
    """

    tray = TrayDesignBlock()
    item = ItemDesignBlock()
    render = blocks.ChoiceBlock(
        choices=RENDER_CHOICES, default="thumbnail", required=False
    )
    fallback = blocks.ChoiceBlock(
        choices=FALLBACK_CHOICES, default="icon", required=False
    )

    class Meta:
        icon = "sliders"
        collapsed = True
        migration_key = "wagtail_daisIE.InputWidgetDesignBlock"
        form_layout = blocks.BlockGroup(
            children=[
                "typography",
                "render",
                "fallback",
                "tray",
                "item",
                "size",
                "background",
                "border",
                "padding",
                "margin",
                "box",
            ],
            heading=_("Input design"),
        )
