from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel
from wagtail.models import (
    Orderable,
)

from wagtail_daisIE.panels import (
    DaisyUISizePanel,
)

from .fields import DaisyUISizeField


class DaisyUIThemeRadii(Orderable):
    theme = ParentalKey(
        "wagtail_daisIE.DaisyUITheme",
        on_delete=models.CASCADE,
        related_name="radii",
    )
    box = DaisyUISizeField(
        verbose_name=_("Box border radius"),
        help_text=_("For card, modal, alert UI"),
        default="0.5rem",
    )
    field = DaisyUISizeField(
        verbose_name=_("Field border radius"),
        help_text=_("For button, input, select, tab UI"),
        default="0.25rem",
    )
    selector = DaisyUISizeField(
        verbose_name=_("Selector border radius"),
        help_text=_("For checkbox, toggle, badge UI"),
        default="1rem",
    )

    panels = [
        DaisyUISizePanel("box"),
        DaisyUISizePanel("field"),
        DaisyUISizePanel("selector"),
    ]

    def __str__(self):
        return f"{self.theme} {_('border radii')}"


class DaisyUIThemeSizes(Orderable):
    theme = ParentalKey(
        "wagtail_daisIE.DaisyUITheme",
        on_delete=models.CASCADE,
        related_name="sizes",
    )
    field = DaisyUISizeField(
        verbose_name=_("Field base size"),
        help_text=_("For button, input, select, tab UI"),
        default="0.25rem",
    )
    selector = DaisyUISizeField(
        verbose_name=_("Selector base size"),
        help_text=_("For checkbox, toggle, badge UI"),
        default="0.25rem",
    )
    border = DaisyUISizeField(
        verbose_name=_("Border width"),
        help_text=_("For all elements"),
        default="1px",
    )

    panels = [
        DaisyUISizePanel("field"),
        DaisyUISizePanel("selector"),
        DaisyUISizePanel("border"),
    ]

    def __str__(self):
        return f"{self.theme} {_('sizes')}"


class DaisyUIThemeEffects(Orderable):
    theme = ParentalKey(
        "wagtail_daisIE.DaisyUITheme",
        on_delete=models.CASCADE,
        related_name="effects",
    )
    depth = models.BooleanField(
        verbose_name=_("Depth effect"),
        help_text=_("Add 3D depth on fields & selectors"),
        default=True,
    )
    noise = models.BooleanField(
        verbose_name=_("Noise effect"),
        help_text=_("Add noise pattern on fields & selectors"),
        default=False,
    )

    panels = [
        FieldPanel("depth"),
        FieldPanel("noise"),
    ]

    def __str__(self):
        return f"{self.theme} {_('effects')}"
