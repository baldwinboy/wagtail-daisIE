from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import (
    DAISYUI_TEXT_COLOR_CHOICES,
    DECORATION_COLOR_CHOICES,
    DECORATION_THICKNESS_CHOICES,
    FONT_SIZE_CHOICES,
    FONT_WEIGHT_CHOICES,
    LETTER_SPACING_CHOICES,
    LINE_HEIGHT_CHOICES,
    TEXT_ALIGN_CHOICES,
    TEXT_DECORATION_CHOICES,
)
from wagtail_daisIE.widgets import (
    DaisyUIAlignWidget,
    DaisyUISliderWidget,
    DaisyUISwatchWidget,
)

from .css import build_typography_css, merge_block_css
from .fields import ColorChoiceBlock, FontFamilyChoiceBlock


class TypographyStateBlock(blocks.StructBlock):
    """Colour/decoration overrides for one interaction state (hover/active)."""

    text_color = ColorChoiceBlock(
        choices=DAISYUI_TEXT_COLOR_CHOICES,
        default="",
        required=False,
        widget=DaisyUISwatchWidget(prefix="text"),
    )
    text_decoration = blocks.ChoiceBlock(
        choices=TEXT_DECORATION_CHOICES,
        default="",
        required=False,
        label=_("Underline"),
    )
    decoration_color = ColorChoiceBlock(
        choices=DECORATION_COLOR_CHOICES,
        default="",
        required=False,
        label=_("Underline color"),
        widget=DaisyUISwatchWidget(prefix="decoration"),
    )
    decoration_thickness = blocks.ChoiceBlock(
        choices=DECORATION_THICKNESS_CHOICES,
        default="",
        required=False,
        label=_("Underline thickness"),
    )

    class Meta:
        icon = "sliders"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "text_color",
                "text_decoration",
                "decoration_color",
                "decoration_thickness",
            ],
            heading=_("State"),
        )


class TypographyBlock(blocks.StructBlock):
    text_color = ColorChoiceBlock(
        choices=DAISYUI_TEXT_COLOR_CHOICES,
        default="",
        required=False,
        widget=DaisyUISwatchWidget(prefix="text"),
    )
    font_family = FontFamilyChoiceBlock(
        default="",
        required=False,
    )
    font_size = blocks.ChoiceBlock(
        choices=FONT_SIZE_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )
    font_weight = blocks.ChoiceBlock(
        choices=FONT_WEIGHT_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )
    text_align = blocks.ChoiceBlock(
        choices=TEXT_ALIGN_CHOICES,
        default="",
        required=False,
        label=_("Text alignment"),
        widget=DaisyUIAlignWidget(),
    )
    line_height = blocks.ChoiceBlock(
        choices=LINE_HEIGHT_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )
    letter_spacing = blocks.ChoiceBlock(
        choices=LETTER_SPACING_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )
    text_decoration = blocks.ChoiceBlock(
        choices=TEXT_DECORATION_CHOICES,
        default="",
        required=False,
        label=_("Underline"),
    )
    decoration_color = ColorChoiceBlock(
        choices=DECORATION_COLOR_CHOICES,
        default="",
        required=False,
        label=_("Underline color"),
        widget=DaisyUISwatchWidget(prefix="decoration"),
    )
    decoration_thickness = blocks.ChoiceBlock(
        choices=DECORATION_THICKNESS_CHOICES,
        default="",
        required=False,
        label=_("Underline thickness"),
    )
    hover = TypographyStateBlock(required=False, label=_("Hover state"))
    active = TypographyStateBlock(required=False, label=_("Active state"))

    class Meta:
        icon = "pilcrow"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "text_color",
                "font_family",
                "font_size",
                "font_weight",
                "text_align",
                "line_height",
                "letter_spacing",
                "text_decoration",
                "decoration_color",
                "decoration_thickness",
                "hover",
                "active",
            ],
            heading=_("Text styles"),
        )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["block_css"] = merge_block_css(
            parent_context, build_typography_css(value)
        )
        return context
