from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import (
    DAISYUI_TEXT_COLOR_CHOICES,
    FONT_SIZE_CHOICES,
    FONT_WEIGHT_CHOICES,
    LETTER_SPACING_CHOICES,
    LINE_HEIGHT_CHOICES,
    TEXT_ALIGN_CHOICES,
)
from wagtail_daisIE.widgets import (
    DaisyUIAlignWidget,
    DaisyUISliderWidget,
    DaisyUISwatchWidget,
)

from .css import build_typography_css, merge_block_css
from .fields import ColorChoiceBlock, FontFamilyChoiceBlock


class TypographyBlock(blocks.StructBlock):
    text_color = ColorChoiceBlock(
        choices=DAISYUI_TEXT_COLOR_CHOICES,
        default="",
        required=False,
        label=_("Text color"),
        widget=DaisyUISwatchWidget(prefix="text"),
    )
    font_family = FontFamilyChoiceBlock(
        default="",
        required=False,
        label=_("Font family"),
    )
    font_size = blocks.ChoiceBlock(
        choices=FONT_SIZE_CHOICES,
        default="",
        required=False,
        label=_("Font size"),
        widget=DaisyUISliderWidget(),
    )
    font_weight = blocks.ChoiceBlock(
        choices=FONT_WEIGHT_CHOICES,
        default="",
        required=False,
        label=_("Font weight"),
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
        label=_("Line height"),
        widget=DaisyUISliderWidget(),
    )
    letter_spacing = blocks.ChoiceBlock(
        choices=LETTER_SPACING_CHOICES,
        default="",
        required=False,
        label=_("Letter spacing"),
        widget=DaisyUISliderWidget(),
    )

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
            ],
            heading=_("Text styles"),
        )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["block_css"] = merge_block_css(
            parent_context, build_typography_css(value)
        )
        return context
