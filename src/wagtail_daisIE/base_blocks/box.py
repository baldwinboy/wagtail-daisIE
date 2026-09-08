from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import (
    BORDER_STYLE_CHOICES,
    DAISYUI_BORDER_COLOR_CHOICES,
    GAP_CHOICES,
    MARGIN_CHOICES,
    PADDING_CHOICES,
    ROUNDED_CHOICES,
    SHADOW_CHOICES,
)
from wagtail_daisIE.widgets import (
    DaisyUIIntegerBlock,
    DaisyUINumberSliderWidget,
    DaisyUISliderWidget,
    DaisyUISwatchWidget,
)

from .css import (
    build_border_css,
    build_box_css,
    build_margin_css,
    build_padding_css,
    build_spacing_css,
    merge_block_css,
)
from .fields import ColorChoiceBlock


class BorderBlock(blocks.StructBlock):
    border_width = DaisyUIIntegerBlock(
        default=None,
        required=False,
        max_value=999,
        label=_("Border width"),
        help_text=_("Border width in pixels."),
        widget=DaisyUINumberSliderWidget(
            min_value=0, max_value=999, step=1, suffix="px"
        ),
    )
    border_color = ColorChoiceBlock(
        choices=DAISYUI_BORDER_COLOR_CHOICES,
        default="",
        required=False,
        label=_("Border color"),
        widget=DaisyUISwatchWidget(prefix="border"),
    )
    border_style = blocks.ChoiceBlock(
        choices=BORDER_STYLE_CHOICES,
        default="",
        required=False,
        label=_("Border style"),
    )

    class Meta:
        icon = "minus"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "border_width",
                "border_color",
                "border_style",
            ],
            heading=_("Border"),
        )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["block_css"] = merge_block_css(parent_context, build_border_css(value))
        return context


class PaddingBlock(blocks.StructBlock):
    all_padding = blocks.ChoiceBlock(
        choices=PADDING_CHOICES["ALL"],
        default="",
        required=False,
        label=_("All Padding"),
        help_text=_(
            "Padding for all sides.Use the individual padding fields for more control."
        ),
        widget=DaisyUISliderWidget(),
    )
    top = blocks.ChoiceBlock(
        choices=PADDING_CHOICES["TOP"],
        default="",
        required=False,
        label=_("Top Padding"),
        widget=DaisyUISliderWidget(),
    )
    right = blocks.ChoiceBlock(
        choices=PADDING_CHOICES["RIGHT"],
        default="",
        required=False,
        label=_("Right Padding"),
        widget=DaisyUISliderWidget(),
    )
    bottom = blocks.ChoiceBlock(
        choices=PADDING_CHOICES["BOTTOM"],
        default="",
        required=False,
        label=_("Bottom Padding"),
        widget=DaisyUISliderWidget(),
    )
    left = blocks.ChoiceBlock(
        choices=PADDING_CHOICES["LEFT"],
        default="",
        required=False,
        label=_("Left Padding"),
        widget=DaisyUISliderWidget(),
    )

    class Meta:
        icon = "radio-full"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "all_padding",
                "top",
                "right",
                "bottom",
                "left",
            ],
            heading=_("Padding"),
        )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["block_css"] = merge_block_css(parent_context, build_padding_css(value))
        return context


class MarginBlock(blocks.StructBlock):
    all_margins = blocks.ChoiceBlock(
        choices=MARGIN_CHOICES["ALL"],
        default="",
        required=False,
        label=_("All Margins"),
        help_text=_(
            "Margin for all sides. Use the individual margin fields for more control."
        ),
        widget=DaisyUISliderWidget(),
    )
    top = blocks.ChoiceBlock(
        choices=MARGIN_CHOICES["TOP"],
        default="",
        required=False,
        label=_("Top Margin"),
        widget=DaisyUISliderWidget(),
    )
    right = blocks.ChoiceBlock(
        choices=MARGIN_CHOICES["RIGHT"],
        default="",
        required=False,
        label=_("Right Margin"),
        widget=DaisyUISliderWidget(),
    )
    bottom = blocks.ChoiceBlock(
        choices=MARGIN_CHOICES["BOTTOM"],
        default="",
        required=False,
        label=_("Bottom Margin"),
        widget=DaisyUISliderWidget(),
    )
    left = blocks.ChoiceBlock(
        choices=MARGIN_CHOICES["LEFT"],
        default="",
        required=False,
        label=_("Left Margin"),
        widget=DaisyUISliderWidget(),
    )

    class Meta:
        icon = "radio-empty"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "all_margins",
                "top",
                "right",
                "bottom",
                "left",
            ],
            heading=_("Margin"),
        )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["block_css"] = merge_block_css(parent_context, build_margin_css(value))
        return context


class BoxBlock(blocks.StructBlock):
    rounded = blocks.ChoiceBlock(
        choices=ROUNDED_CHOICES,
        default="",
        required=False,
        label=_("Rounded corners"),
        widget=DaisyUISliderWidget(),
    )
    shadow = blocks.ChoiceBlock(
        choices=SHADOW_CHOICES,
        default="",
        required=False,
        label=_("Shadow"),
        widget=DaisyUISliderWidget(),
    )

    class Meta:
        icon = "bars"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "rounded",
                "shadow",
            ],
            heading=_("Rounded corners, shadow"),
        )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["block_css"] = merge_block_css(parent_context, build_box_css(value))
        return context


class SpacingBlock(blocks.StructBlock):
    all = blocks.ChoiceBlock(
        choices=GAP_CHOICES["ALL"],
        default="",
        required=False,
        label=_("Spacing"),
        help_text=_(
            "Spacing for all sides.Use the individual spacing fields for more control."
        ),
        widget=DaisyUISliderWidget(),
    )

    horizontal = blocks.ChoiceBlock(
        choices=GAP_CHOICES["HORIZONTAL"],
        required=False,
        label=_("Horizontal Spacing"),
        help_text=_(
            "Spacing for horizontal sides."
            "Use the individual spacing fields for more control."
        ),
        widget=DaisyUISliderWidget(),
    )

    vertical = blocks.ChoiceBlock(
        choices=GAP_CHOICES["VERTICAL"],
        required=False,
        label=_("Vertical Spacing"),
        help_text=_(
            "Spacing for vertical sides."
            "Use the individual spacing fields for more control."
        ),
        widget=DaisyUISliderWidget(),
    )

    class Meta:
        icon = "grip"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "all",
                "horizontal",
                "vertical",
            ],
            heading=_("Spacing"),
        )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["block_css"] = merge_block_css(parent_context, build_spacing_css(value))
        return context
