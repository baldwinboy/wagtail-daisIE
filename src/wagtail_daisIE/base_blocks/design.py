from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.base_blocks.button import ButtonAppearanceBlock

from .audience import AudienceBlock, evaluate_audience
from .background import BackgroundBlock, TextBackgroundBlock
from .box import BorderBlock, BoxBlock, MarginBlock, PaddingBlock, SpacingBlock
from .css import build_design_css
from .size import BlockSizeBlock, InlineSizeBlock, MediaSizeBlock
from .table import TableAppearanceBlock
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


class TableDesignBlock(DesignBlock):
    table_appearance = TableAppearanceBlock()

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "table_appearance",
                *_BLOCK_CHILDREN,
            ],
            heading=_("Design"),
        )


class SpacedDesignBlock(DesignBlock):
    spacing = SpacingBlock()

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=_SPACED_CHILDREN,
            heading=_("Design"),
        )


class PageDesignBlock(blocks.StructBlock):
    """Page-wide defaults applied per element category.

    Editors set default container, text, button and media styles once; each
    themed block inherits only the defaults for its own category (via the
    ``<category>_css`` context channels) so categories never bleed into each
    other. Per-block settings are applied on top.
    """

    container = SpacedDesignBlock()
    text = TypographyDesignBlock()
    button = ButtonDesignBlock()
    media = MediaDesignBlock()

    class Meta:
        icon = "sliders"
        label = _("Page default design")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=["container", "text", "button", "media"],
            heading=_("Default design"),
        )

    def get_default_css(self, value):
        """Return a ``{category: css}`` mapping for the block's design fields."""
        return {
            name: build_design_css((value or {}).get(name))
            for name in self.child_blocks
        }


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

    default_css_key = "container"

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        parent_context = parent_context or {}
        key = f"{self.default_css_key}_css"
        channel = parent_context.get(key, "")
        own = build_design_css(value.get("design"))
        context["block_css"] = build_class(
            channel,
            parent_context.get("menu_default_css", ""),
            own,
        )
        context[key] = build_class(channel, own)
        audience_keys = (value.get("audience") or {}).get("audience") or []
        request = parent_context.get("request")
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
    default_css_key = "media"

    class Meta:
        abstract = True


class ThemedSpacedBlock(ThemedBlock):
    design = SpacedDesignBlock()

    class Meta:
        abstract = True


class ThemedTypographyBlock(ThemedBlock):
    design = TypographyDesignBlock()
    default_css_key = "text"

    class Meta:
        abstract = True


class ThemedButtonBlock(ThemedBlock):
    design = ButtonDesignBlock()
    default_css_key = "button"

    class Meta:
        abstract = True


class ThemedTableBlock(ThemedBlock):
    design = TableDesignBlock()
    cell_design = TypographyDesignBlock()
    header_cell_design = TypographyDesignBlock()

    class Meta:
        abstract = True

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        parent_context = parent_context or {}
        inherited = build_class(
            parent_context.get("text_css", ""),
            parent_context.get("cell_css", ""),
        )
        cell_css = build_class(inherited, build_design_css(value.get("cell_design")))
        header_cell_css = build_class(
            cell_css, build_design_css(value.get("header_cell_design"))
        )
        context["cell_css"] = cell_css
        context["header_cell_css"] = header_cell_css
        return context


class PublicThemedBlock(ThemedBlock):
    design = DesignBlock()

    class Meta:
        abstract = True


class PublicThemedMediaBlock(ThemedBlock):
    design = MediaDesignBlock()
    default_css_key = "media"

    class Meta:
        abstract = True
