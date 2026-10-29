"""Editor design vocabulary for file/attachment input widgets.

``TrayDesignBlock`` styles the container that holds uploaded items;
``ItemDesignBlock`` styles a single item (token/card/avatar). Both are compact
blocks, so adding them to a block's design does not change its migration
representation. The ``render``/``fallback`` choices below drive which markup a
dynamic item clones and what shows when there is nothing to display.

``InputWidgetDesignBlock`` styles the input element itself; upload-only controls
live in ``UploadWidgetDesignBlock``.
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
    GRID_COLUMN_CHOICES,
    JUSTIFY_CHOICES,
    MAIN_LAYOUT_CHOICES,
)

from .compact import DaisieStructBlock
from .design import SpacedDesignBlock, TypographyDesignBlock
from .responsive import responsive_overrides


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
    columns = blocks.ChoiceBlock(
        choices=GRID_COLUMN_CHOICES,
        required=False,
        label=_("Columns"),
        help_text=_("Used when the layout is a grid."),
    )
    wrap = blocks.ChoiceBlock(
        choices=FLEX_WRAP_CHOICES, required=False, label=_("Wrap")
    )
    justify = blocks.ChoiceBlock(choices=JUSTIFY_CHOICES, required=False)
    align = blocks.ChoiceBlock(choices=ALIGNMENT_CHOICES, required=False)
    gap = blocks.ChoiceBlock(choices=GAP_CHOICES["ALL"], required=False)
    responsive = responsive_overrides()

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "layout",
                "columns",
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
                "responsive",
            ],
            heading=_("Tray design"),
        )


class ItemDesignBlock(TypographyDesignBlock):
    shape = blocks.ChoiceBlock(
        choices=AVATAR_SHAPE_CHOICES,
        required=False,
        label=_("Shape"),
    )
    responsive = responsive_overrides()

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
                "responsive",
            ],
            heading=_("Item design"),
        )


class InputWidgetDesignBlock(TypographyDesignBlock):
    """Editor design for a form input.

    A frozen migration key keeps future edits from disturbing
    ``DaisieFormField.input_design`` migrations. Upload-only controls live in
    :class:`UploadWidgetDesignBlock`.
    """

    responsive = responsive_overrides()

    class Meta:
        icon = "sliders"
        collapsed = True
        migration_key = "wagtail_daisIE.InputWidgetDesignBlock"
        form_layout = blocks.BlockGroup(
            children=[
                "typography",
                "size",
                "background",
                "border",
                "padding",
                "margin",
                "box",
                "responsive",
            ],
            heading=_("Input design"),
        )


class UploadWidgetDesignBlock(DaisieStructBlock):
    """Upload-only design controls for a file/attachment form field."""

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
        label = _("Upload design")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=["render", "fallback", "tray", "item"],
            heading=_("Upload design"),
        )
