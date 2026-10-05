"""Email-specific design composites.

MJML components only support a subset of the web background API:

* ``mj-section``, ``mj-wrapper`` and ``mj-hero`` accept a background image, so
  they use a :class:`BackgroundStreamBlock` restricted to solid and image
  layers (gradients are never supported by any MJML component).
* every other component only accepts a solid background colour, so they use
  :class:`TextBackgroundBlock`.
* ``mj-navbar`` has no background attribute at all, so its design omits the
  field entirely.

The composites subclass the web design blocks so all other design groups
(typography, spacing, box, ...) stay identical.
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ...base_blocks import (
    BlockSizeBlock,
    BorderBlock,
    BoxBlock,
    MarginBlock,
    PaddingBlock,
)
from ...base_blocks.background import TextBackgroundBlock
from ...base_blocks.background_layer import BackgroundStreamBlock
from ...base_blocks.compact import DaisieStructBlock
from ...base_blocks.design import (
    ButtonDesignBlock,
    DesignBlock,
    MediaDesignBlock,
    SpacedDesignBlock,
    TypographyDesignBlock,
)


#: Layer types MJML can render a background with.
EMAIL_BACKGROUND_TYPES = ("solid", "image")


class EmailImageDesignBlock(DesignBlock):
    background = BackgroundStreamBlock(allowed_types=EMAIL_BACKGROUND_TYPES)


class EmailImageSpacedDesignBlock(SpacedDesignBlock):
    background = BackgroundStreamBlock(allowed_types=EMAIL_BACKGROUND_TYPES)


class EmailSolidDesignBlock(DesignBlock):
    background = TextBackgroundBlock()


class EmailSolidSpacedDesignBlock(SpacedDesignBlock):
    background = TextBackgroundBlock()


class EmailSolidTypographyDesignBlock(TypographyDesignBlock):
    background = TextBackgroundBlock()


class EmailSolidButtonDesignBlock(ButtonDesignBlock):
    background = TextBackgroundBlock()


class EmailSolidMediaDesignBlock(MediaDesignBlock):
    background = TextBackgroundBlock()


class EmailNavbarDesignBlock(DaisieStructBlock):
    """The design groups ``mj-navbar`` supports (no background)."""

    size = BlockSizeBlock()
    border = BorderBlock()
    padding = PaddingBlock()
    margin = MarginBlock()
    box = BoxBlock()

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=["size", "border", "padding", "margin", "box"],
            heading=_("Design"),
        )


__all__ = [
    "EMAIL_BACKGROUND_TYPES",
    "EmailImageDesignBlock",
    "EmailImageSpacedDesignBlock",
    "EmailNavbarDesignBlock",
    "EmailSolidButtonDesignBlock",
    "EmailSolidDesignBlock",
    "EmailSolidMediaDesignBlock",
    "EmailSolidSpacedDesignBlock",
    "EmailSolidTypographyDesignBlock",
]
