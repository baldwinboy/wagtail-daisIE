from django import forms
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.admin.telepath import register
from wagtail.blocks.struct_block import StructBlockAdapter
from wagtail.images.blocks import ImageChooserBlock

from wagtail_daisIE.choices import DAISYUI_BG_COLOR_CHOICES
from wagtail_daisIE.choices.utils import ChoiceList
from wagtail_daisIE.widgets import (
    DaisyUIIntegerBlock,
    DaisyUINumberSliderWidget,
    DaisyUIRawSwatchWidget,
)

from .compact import DaisieStreamBlock, DaisieStructBlock
from .fields import ColorChoiceBlock


class BlockBackgroundLayerType(models.TextChoices):
    SOLID = "solid", _("Solid colour")
    IMAGE = "image", _("Image")
    GRADIENT = "gradient", _("Gradient")


class BlockGradientShape(models.TextChoices):
    LINEAR = "linear", _("Linear")
    RADIAL = "radial", _("Radial")
    CONIC = "conic", _("Conic")
    REPEATING_LINEAR = "repeating-linear", _("Repeating Linear")
    REPEATING_RADIAL = "repeating-radial", _("Repeating Radial")
    REPEATING_CONIC = "repeating-conic", _("Repeating Conic")


BACKGROUND_LAYER_TYPE_CHOICES = ChoiceList(
    list(BlockBackgroundLayerType.choices), "BACKGROUND_LAYER_TYPE_CHOICES"
)
GRADIENT_SHAPE_CHOICES = ChoiceList(
    list(BlockGradientShape.choices), "GRADIENT_SHAPE_CHOICES"
)
BACKGROUND_SIZE_CHOICES = ChoiceList(
    [
        ("auto", _("Auto")),
        ("cover", _("Cover")),
        ("contain", _("Contain")),
    ],
    "BACKGROUND_SIZE_CHOICES",
)


class GradientStopBlock(DaisieStructBlock):
    bg_color = ColorChoiceBlock(
        choices=DAISYUI_BG_COLOR_CHOICES,
        default="bg-primary",
        required=False,
        label=_("Background color"),
        widget=DaisyUIRawSwatchWidget(prefix="bg"),
    )
    position = DaisyUIIntegerBlock(
        default=0,
        required=False,
        verbose_name=_("Position"),
        help_text=_("e.g. '0%' or '100%'"),
        min_value=0,
        max_value=100,
        widget=DaisyUINumberSliderWidget(
            min_value=0, max_value=100, step=1, suffix="%"
        ),
    )

    class Meta:
        icon = "pick"
        label = _("Gradient stop")
        collapsed = True


class BackgroundLayerBlock(DaisieStructBlock):
    def __init__(self, *args, allowed_types=None, **kwargs):
        """Optionally restrict the selectable layer types.

        Email components only support a subset (solid or image, never
        gradient), so the email design composites construct the block with
        ``allowed_types``. The restricted ``layer_type`` choice is injected as
        a local block, leaving the shared class definition untouched.
        """
        local_blocks = list(kwargs.pop("local_blocks", None) or [])
        if allowed_types is not None:
            choices = [
                choice
                for choice in BACKGROUND_LAYER_TYPE_CHOICES
                if choice[0] in allowed_types
            ]
            local_blocks.append(
                (
                    "layer_type",
                    blocks.ChoiceBlock(
                        max_length=10,
                        choices=choices,
                        default=choices[0][0] if choices else "",
                        verbose_name=_("Layer type"),
                        classname="background-layer-form",
                    ),
                )
            )
        super().__init__(*args, local_blocks=local_blocks, **kwargs)

    layer_type = blocks.ChoiceBlock(
        max_length=10,
        choices=BACKGROUND_LAYER_TYPE_CHOICES,
        default=BlockBackgroundLayerType.SOLID,
        verbose_name=_("Layer type"),
        classname="background-layer-form",
    )
    color = ColorChoiceBlock(
        choices=DAISYUI_BG_COLOR_CHOICES,
        default="bg-primary",
        required=False,
        label=_("Background color"),
        widget=DaisyUIRawSwatchWidget(prefix="bg"),
        classname="layer-solid",
    )
    image = ImageChooserBlock(required=False, classname="layer-image")
    position = blocks.CharBlock(
        max_length=64,
        default="center",
        required=False,
        verbose_name=_("Position"),
        help_text=_("CSS background-position, e.g. center, 50%, 10px."),
        classname="layer-image",
    )
    size = blocks.ChoiceBlock(
        max_length=64,
        choices=BACKGROUND_SIZE_CHOICES,
        default="cover",
        verbose_name=_("Size"),
        classname="layer-image",
    )
    repeat = blocks.BooleanBlock(
        default=False,
        required=False,
        verbose_name=_("Repeat"),
        classname="layer-image",
    )
    gradient_shape = blocks.ChoiceBlock(
        max_length=64,
        required=False,
        choices=GRADIENT_SHAPE_CHOICES,
        default=BlockGradientShape.LINEAR,
        verbose_name=_("Gradient shape"),
        help_text=_("e.g. 'linear', 'radial', 'conic'"),
        classname="layer-gradient",
    )
    gradient_angle = DaisyUIIntegerBlock(
        default=0,
        required=False,
        verbose_name=_("Gradient angle"),
        help_text=_("e.g. 0, 90, 180, 270"),
        min_value=0,
        max_value=360,
        widget=DaisyUINumberSliderWidget(
            min_value=0, max_value=360, step=1, suffix="deg"
        ),
        classname="layer-gradient",
    )
    gradient_stops = blocks.ListBlock(
        GradientStopBlock(),
        required=False,
        form_classname="layer-gradient",
    )

    class Meta:
        icon = "pick"
        label = _("Background layer")
        collapsed = True

    def __str__(self):
        return str(_("Background layer"))

    def get_solid_css(self, value):
        """Build a CSS background layer string from the block value."""
        layer_type = (value or {}).get("layer_type")
        color = (value or {}).get("color")
        if layer_type == BlockBackgroundLayerType.SOLID and color:
            return color
        return ""

    def get_image_css(self, value):
        """Build a CSS background layer string from the block value."""
        layer_type = (value or {}).get("layer_type")
        image = (value or {}).get("image")
        if layer_type == BlockBackgroundLayerType.IMAGE and image:
            try:
                img_url = image.file.url
            except Exception:
                return ""
            pos = (value or {}).get("position") or "center"
            size = (value or {}).get("size") or "cover"
            repeat = "repeat" if (value or {}).get("repeat") else "no-repeat"
            return f"url('{img_url}') {pos} / {size} {repeat}"
        return ""

    def get_gradient_css(self, value):
        """Build a CSS background layer string from the block value."""
        layer_type = (value or {}).get("layer_type")
        gradient_shape = (value or {}).get("gradient_shape")
        gradient_angle = (value or {}).get("gradient_angle")
        if layer_type == BlockBackgroundLayerType.GRADIENT and gradient_shape:
            gradient_direction = f"{gradient_angle}deg"
            stops = (value or {}).get("gradient_stops") or []
            if stops:
                stops_css = ", ".join(
                    f"{stop.get('bg_color')} {stop.get('position')}%" for stop in stops
                )
                return f"{gradient_shape}-gradient({gradient_direction}, {stops_css})"
            return ""
        return ""

    def get_css(self, value):
        """Build a CSS background layer string from the block value."""
        layer_type = (value or {}).get("layer_type")
        if layer_type == BlockBackgroundLayerType.SOLID:
            return self.get_solid_css(value)
        elif layer_type == BlockBackgroundLayerType.IMAGE:
            return self.get_image_css(value)
        elif layer_type == BlockBackgroundLayerType.GRADIENT:
            return self.get_gradient_css(value)
        return ""


class BackgroundStreamBlock(DaisieStreamBlock):
    layer = BackgroundLayerBlock()

    def __init__(self, *args, allowed_types=None, required=False, **kwargs):
        kwargs.setdefault("required", required)
        if allowed_types is not None:
            local_blocks = list(kwargs.pop("local_blocks", None) or [])
            local_blocks.append(
                ("layer", BackgroundLayerBlock(allowed_types=allowed_types))
            )
            kwargs["local_blocks"] = local_blocks
        super().__init__(*args, **kwargs)

    class Meta:
        icon = "pick"
        label = _("Background layers")

    def get_css(self, values):
        """Build a combined CSS background value from all layers."""
        css_layers = []
        for value in values or []:
            if getattr(value, "block_type", None) == "layer":
                css = value.block.get_css(value.value)
                if css:
                    css_layers.append(css)
        return ", ".join(css_layers) if css_layers else ""


class BackgroundLayerBlockAdapter(StructBlockAdapter):
    js_constructor = "wagtail_daisIE.base_blocks.BackgroundLayerBlock"

    @cached_property
    def media(self):
        structblock_media = super().media
        return forms.Media(
            js=[
                *structblock_media._js,
                "wagtail_daisIE/js/background_layer_block.js",
            ],
            css=structblock_media._css,
        )


register(BackgroundLayerBlockAdapter(), BackgroundLayerBlock)
