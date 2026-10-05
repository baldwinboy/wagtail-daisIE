from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import (
    BLOCK_HEIGHT_CHOICES,
    BLOCK_MAX_HEIGHT_CHOICES,
    BLOCK_MAX_WIDTH_CHOICES,
    BLOCK_MIN_HEIGHT_CHOICES,
    BLOCK_MIN_WIDTH_CHOICES,
    BLOCK_SIZE_CHOICES,
    BLOCK_WIDTH_CHOICES,
    INLINE_HEIGHT_CHOICES,
    INLINE_MAX_HEIGHT_CHOICES,
    INLINE_MAX_WIDTH_CHOICES,
    INLINE_MIN_HEIGHT_CHOICES,
    INLINE_MIN_WIDTH_CHOICES,
    INLINE_SIZE_CHOICES,
    INLINE_WIDTH_CHOICES,
)
from wagtail_daisIE.widgets import DaisyUISliderWidget

from .compact import DaisieStructBlock
from .css import build_media_size_css, build_size_css, merge_block_css
from .utils import validate_aspect


class SizeContextMixin:
    """Expose the computed utility classes as ``block_css``."""

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["block_css"] = merge_block_css(parent_context, build_size_css(value))
        return context


class MediaSizeContextMixin:
    """Expose the computed utility classes as ``block_css``."""

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["block_css"] = merge_block_css(
            parent_context, build_media_size_css(value)
        )
        return context


class InlineWidthBlock(SizeContextMixin, DaisieStructBlock):
    width = blocks.ChoiceBlock(
        choices=INLINE_WIDTH_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )
    min_width = blocks.ChoiceBlock(
        choices=INLINE_MIN_WIDTH_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )
    max_width = blocks.ChoiceBlock(
        choices=INLINE_MAX_WIDTH_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )

    class Meta:
        icon = "expand-right"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "width",
                "min_width",
                "max_width",
            ],
            heading=_("Inline width"),
        )


class InlineHeightBlock(SizeContextMixin, DaisieStructBlock):
    height = blocks.ChoiceBlock(
        choices=INLINE_HEIGHT_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )
    min_height = blocks.ChoiceBlock(
        choices=INLINE_MIN_HEIGHT_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )
    max_height = blocks.ChoiceBlock(
        choices=INLINE_MAX_HEIGHT_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )

    class Meta:
        icon = "expand-right"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "height",
                "min_height",
                "max_height",
            ],
            heading=_("Inline height"),
        )


class InlineSizeBlock(SizeContextMixin, DaisieStructBlock):
    size = blocks.ChoiceBlock(
        choices=INLINE_SIZE_CHOICES,
        default="",
        required=False,
        help_text=_("Size for inline elements."),
        widget=DaisyUISliderWidget(),
    )
    width = InlineWidthBlock()
    height = InlineHeightBlock()

    class Meta:
        icon = "breadcrumb-expand"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "size",
                "width",
                "height",
            ],
            heading=_("Size"),
        )


class BlockWidthBlock(SizeContextMixin, DaisieStructBlock):
    width = blocks.ChoiceBlock(
        choices=BLOCK_WIDTH_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )
    min_width = blocks.ChoiceBlock(
        choices=BLOCK_MIN_WIDTH_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )
    max_width = blocks.ChoiceBlock(
        choices=BLOCK_MAX_WIDTH_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )

    class Meta:
        icon = "expand-right"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "width",
                "min_width",
                "max_width",
            ],
            heading=_("Block width"),
        )


class BlockHeightBlock(SizeContextMixin, DaisieStructBlock):
    height = blocks.ChoiceBlock(
        choices=BLOCK_HEIGHT_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )
    min_height = blocks.ChoiceBlock(
        choices=BLOCK_MIN_HEIGHT_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )
    max_height = blocks.ChoiceBlock(
        choices=BLOCK_MAX_HEIGHT_CHOICES,
        default="",
        required=False,
        widget=DaisyUISliderWidget(),
    )

    class Meta:
        icon = "expand-right"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "height",
                "min_height",
                "max_height",
            ],
            heading=_("Block height"),
        )


class AbstractBlockSizeBlock(DaisieStructBlock):
    size = blocks.ChoiceBlock(
        choices=BLOCK_SIZE_CHOICES,
        default="",
        required=False,
        help_text=_("Size for block elements."),
        widget=DaisyUISliderWidget(),
    )
    width = BlockWidthBlock()
    height = BlockHeightBlock()

    class Meta:
        abstract = True


class BlockSizeBlock(SizeContextMixin, AbstractBlockSizeBlock):
    class Meta:
        icon = "breadcrumb-expand"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "size",
                "width",
                "height",
            ],
            heading=_("Size"),
        )


class AspectBlock(blocks.TextBlock):
    def clean(self, value):
        value = super().clean(value)
        if value:
            return value.lower()
        return value


class MediaSizeBlock(MediaSizeContextMixin, AbstractBlockSizeBlock):
    aspect = AspectBlock(
        default="",
        required=False,
        label=_("Aspect ratio"),
        help_text=_("Aspect ratio: square, video or 16:9."),
        validators=[validate_aspect],
    )

    class Meta:
        icon = "breadcrumb-expand"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "aspect",
                "size",
                "width",
                "height",
            ],
            heading=_("Size"),
        )
