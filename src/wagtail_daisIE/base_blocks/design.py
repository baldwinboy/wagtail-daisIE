from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.base_blocks.button import ButtonAppearanceBlock

from .audience import AudienceBlock, evaluate_audience
from .background import BackgroundBlock, TextBackgroundBlock
from .box import BorderBlock, BoxBlock, MarginBlock, PaddingBlock, SpacingBlock
from .css import build_design_css
from .size import BlockSizeBlock, InlineSizeBlock, MediaSizeBlock
from .typography import TypographyBlock
from .utils import build_class


_BOX_CHILDREN = [
    "background",
    "border",
    "padding",
    "margin",
    "box",
]

_BLOCK_CHILDREN = [
    "size",
    *_BOX_CHILDREN,
]

_SPACED_CHILDREN = [
    "size",
    "spacing",
    *_BOX_CHILDREN,
]


class BaseDesignBlock(blocks.StructBlock):
    padding = PaddingBlock()
    margin = MarginBlock()
    box = BoxBlock()
    border = BorderBlock()

    class Meta:
        abstract = True


class TypographyDesignBlock(BaseDesignBlock):
    background = TextBackgroundBlock()
    size = InlineSizeBlock()
    typography = TypographyBlock()

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "typography",
                *_BLOCK_CHILDREN,
            ],
            heading=_("Design"),
        )


class InlineDesignBlock(BaseDesignBlock):
    background = BackgroundBlock()
    size = InlineSizeBlock()

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=_BLOCK_CHILDREN,
            heading=_("Design"),
        )


class InlineSpacedDesignBlock(InlineDesignBlock):
    spacing = SpacingBlock()

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=_SPACED_CHILDREN,
            heading=_("Design"),
        )


class ButtonDesignBlock(InlineSpacedDesignBlock):
    button_appearance = ButtonAppearanceBlock()

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "button_appearance",
                *_SPACED_CHILDREN,
            ],
            heading=_("Design"),
        )


class DesignBlock(BaseDesignBlock):
    background = BackgroundBlock()
    size = BlockSizeBlock()

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=_BLOCK_CHILDREN,
            heading=_("Design"),
        )


class MediaDesignBlock(DesignBlock):
    size = MediaSizeBlock()


class SpacedDesignBlock(DesignBlock):
    spacing = SpacingBlock()

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=_SPACED_CHILDREN,
            heading=_("Design"),
        )


class MenuItemDesignBlock(TypographyDesignBlock):
    """Default design applied to every item in a menu.

    Editors set menu-wide font, text colour, background, spacing and size
    defaults here; each item's own design is appended after these classes so
    per-block settings can still win (see :func:`build_design_css`).
    """

    spacing = SpacingBlock()

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "typography",
                "size",
                "spacing",
                "background",
                "border",
                "padding",
                "margin",
                "box",
            ],
            heading=_("Menu item defaults"),
        )


class ThemedBlock(blocks.StructBlock):
    audience = AudienceBlock()
    design = DesignBlock()

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        inherited = (parent_context or {}).get("block_css", "")
        context["block_css"] = build_class(
            inherited, build_design_css(value.get("design"))
        )
        audience_keys = (value.get("audience") or {}).get("audience") or []
        request = (parent_context or {}).get("request")
        context["audience_allowed"] = evaluate_audience(audience_keys, request)
        return context

    class Meta:
        abstract = True
        form_layout = blocks.BlockGroup(
            children=[],
            settings=["design", "audience"],
        )


class ThemedMediaBlock(ThemedBlock):
    design = MediaDesignBlock()

    class Meta:
        abstract = True


class ThemedSpacedBlock(ThemedBlock):
    design = SpacedDesignBlock()

    class Meta:
        abstract = True


class ThemedTypographyBlock(ThemedBlock):
    design = TypographyDesignBlock()

    class Meta:
        abstract = True


class ThemedButtonBlock(ThemedBlock):
    design = ButtonDesignBlock()

    class Meta:
        abstract = True


class PublicThemedBlock(ThemedBlock):
    design = DesignBlock()

    class Meta:
        abstract = True
        form_layout = blocks.BlockGroup(
            children=[],
            settings=["design"],
        )


class PublicThemedMediaBlock(ThemedBlock):
    design = MediaDesignBlock()

    class Meta:
        abstract = True
        form_layout = blocks.BlockGroup(
            children=[],
            settings=["design"],
        )
