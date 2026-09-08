from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.models import (
    Orderable,
)

from wagtail_daisIE.panels import (
    GradientStopColorPanel,
    LayerColorPanel,
)

from .fields import DaisyUIColorField


class DaisyUIThemeBackgroundLayerType(models.TextChoices):
    SOLID = "solid", _("Solid colour")
    IMAGE = "image", _("Image")
    GRADIENT = "gradient", _("Gradient")


class DaisyUIThemeBackgroundLayerGradientShape(models.TextChoices):
    LINEAR = "linear-gradient", _("Linear")
    RADIAL = "radial-gradient", _("Radial")
    CONIC = "conic-gradient", _("Conic")
    REPEATING_LINEAR = "repeating-linear-gradient", _("Repeating Linear")
    REPEATING_RADIAL = "repeating-radial-gradient", _("Repeating Radial")
    REPEATING_CONIC = "repeating-conic-gradient", _("Repeating Conic")


class DaisyUIThemeBackground(ClusterableModel, Orderable):
    theme = ParentalKey(
        "wagtail_daisIE.DaisyUITheme",
        on_delete=models.CASCADE,
        related_name="background",
    )

    panels = [
        InlinePanel("layers", label=_("Background layers"), classname="collapsed"),
    ]

    def __str__(self):
        return f"{self.theme} {_('background')}"

    def get_effective_background(self):
        """Return a CSS background value built from all layers."""
        layers = []

        for layer in self.layers.all():
            css = layer.get_css()
            if css:
                layers.append(css)

        if not layers:
            colors = self.theme.colors.first()
            return colors.base_100 if colors else ""

        return ", ".join(layers)


class DaisyUIThemeBackgroundLayer(ClusterableModel, Orderable):
    background = ParentalKey(
        "wagtail_daisIE.DaisyUIThemeBackground",
        on_delete=models.CASCADE,
        related_name="layers",
    )
    layer_type = models.CharField(
        max_length=10,
        choices=DaisyUIThemeBackgroundLayerType.choices,
        default=DaisyUIThemeBackgroundLayerType.SOLID,
        verbose_name=_("Layer type"),
    )
    color = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Colour"),
        help_text=_(
            "Pick a colour from the theme palette or choose any custom colour."
        ),
        null=True,
        blank=True,
    )
    gradient_shape = models.CharField(
        max_length=64,
        blank=True,
        default=DaisyUIThemeBackgroundLayerGradientShape.LINEAR,
        verbose_name=_("Gradient shape"),
        help_text=_("e.g. 'linear', 'radial', 'conic'"),
    )
    gradient_angle = models.PositiveSmallIntegerField(
        default=0,
        blank=True,
        verbose_name=_("Gradient angle"),
        help_text=_("e.g. 0, 90, 180, 270"),
        validators=[MinValueValidator(0), MaxValueValidator(360)],
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Image"),
    )
    position = models.CharField(
        max_length=64,
        default="center",
        blank=True,
        verbose_name=_("Position"),
        help_text=_(
            "CSS background-position value"
            " (e.g. 'center', 'top', 'bottom', 'left', 'right')"
            " or a percentage (e.g. '50%')"
            " or a length (e.g. '10px'). See:"
            " https://developer.mozilla.org/en-US/docs/Web/CSS/background-position"
        ),
    )
    size = models.CharField(
        max_length=64,
        choices=[
            ("auto", _("Auto")),
            ("cover", _("Cover")),
            ("contain", _("Contain")),
        ],
        default="cover",
        verbose_name=_("Size"),
    )
    repeat = models.BooleanField(
        default=False,
        verbose_name=_("Repeat"),
    )

    panels = [
        FieldPanel("layer_type", classname="background-layer-form"),
        MultiFieldPanel(
            [LayerColorPanel("color")],
            heading=_("Solid color"),
            classname="collapsed layer-solid",
        ),
        MultiFieldPanel(
            [
                FieldPanel("gradient_shape"),
                FieldPanel("gradient_angle"),
                InlinePanel(
                    "stops",
                    label=_("Gradient stops"),
                ),
            ],
            heading=_("Gradient"),
            classname="collapsed layer-gradient",
        ),
        MultiFieldPanel(
            [
                FieldPanel("image", classname="layer-image"),
                FieldPanel("position", classname="layer-image"),
                FieldPanel("size", classname="layer-image"),
                FieldPanel("repeat", classname="layer-image"),
            ],
            heading=_("Image"),
            classname="collapsed layer-image",
        ),
    ]

    def __str__(self):
        return f"{self.get_layer_type_display()} layer"

    def get_solid_css(self):
        """Build a CSS background layer string from the block value."""
        layer_type = self.layer_type
        color = self.color
        if layer_type == DaisyUIThemeBackgroundLayerType.SOLID and color:
            return color
        return ""

    def get_image_css(self):
        """Build a CSS background layer string from the block value."""
        layer_type = self.layer_type
        image = self.image
        if layer_type == DaisyUIThemeBackgroundLayerType.IMAGE and image:
            try:
                img_url = image.file.url
            except Exception:
                return ""
            pos = self.position or "center"
            size = self.size or "cover"
            repeat = "repeat" if self.repeat else "no-repeat"
            return f"url('{img_url}') {pos} / {size} {repeat}"
        return ""

    def get_gradient_css(self):
        """Build a CSS background layer string from the block value."""
        layer_type = self.layer_type
        gradient_shape = self.gradient_shape
        gradient_angle = self.gradient_angle
        if layer_type == DaisyUIThemeBackgroundLayerType.GRADIENT and gradient_shape:
            gradient_direction = f"{gradient_angle}deg"
            stops = self.stops.all()
            if stops:
                stops_css = ", ".join(f"{s.color} {s.position}%" for s in stops)
                return f"{gradient_shape}({gradient_direction}, {stops_css})"
            return ""
        return ""

    def get_css(self):
        """Build a CSS background layer string from the block value."""
        layer_type = self.layer_type
        if layer_type == DaisyUIThemeBackgroundLayerType.SOLID:
            return self.get_solid_css()
        elif layer_type == DaisyUIThemeBackgroundLayerType.IMAGE:
            return self.get_image_css()
        elif layer_type == DaisyUIThemeBackgroundLayerType.GRADIENT:
            return self.get_gradient_css()
        return ""


class DaisyUIThemeBackgroundLayerGradientStop(Orderable):
    layer = ParentalKey(
        "wagtail_daisIE.DaisyUIThemeBackgroundLayer",
        on_delete=models.CASCADE,
        related_name="stops",
    )
    color = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Colour"),
    )
    position = models.PositiveSmallIntegerField(
        default=0,
        blank=True,
        verbose_name=_("Position"),
        help_text=_("e.g. '0%' or '100%'"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    panels = [
        GradientStopColorPanel("color"),
        FieldPanel("position"),
    ]

    def __str__(self):
        return f"{self.color} at {self.position}"
