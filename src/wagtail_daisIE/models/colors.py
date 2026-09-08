from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.models import (
    Orderable,
)

from wagtail_daisIE.panels import DaisyUIColorPanel

from .fields import DaisyUIColorField


class DaisyUIThemeColors(Orderable):
    theme = ParentalKey(
        "wagtail_daisIE.DaisyUITheme",
        on_delete=models.CASCADE,
        related_name="colors",
    )
    primary = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Primary theme color"),
        help_text=_("The main color of your theme"),
        default="#422ad5ff",
    )
    primary_content = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Primary theme content color"),
        help_text=_("Foreground content color to use on primary color"),
        default="#e0e7ffff",
    )
    secondary = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Secondary theme color"),
        help_text=_("The secondary color of your theme"),
        default="#f43098ff",
    )
    secondary_content = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Secondary theme content color"),
        help_text=_("Foreground content color to use on secondary color"),
        default="#f9e4f0ff",
    )
    accent = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Accent theme color"),
        help_text=_("The accent color of your theme"),
        default="#00d3bbff",
    )
    accent_content = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Accent theme content color"),
        help_text=_("Foreground content color to use on accent color"),
        default="#084d49ff",
    )
    neutral = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Neutral dark color"),
        help_text=_("For not-saturated parts of UI"),
        default="#0b0809ff",
    )
    neutral_content = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Neutral dark content color"),
        help_text=_("Foreground content color to use on neutral color"),
        default="#e7e3e4ff",
    )
    base_100 = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Base surface color of page"),
        help_text=_("Used for blank backgrounds"),
        default="#ffffffff",
    )
    base_200 = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Base color, darker shade"),
        help_text=_("To create elevations"),
        default="#f8f8f8ff",
    )
    base_300 = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Base color, even darker shade"),
        help_text=_("To create elevations"),
        default="#eeeeeeff",
    )
    base_content = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Base content color"),
        help_text=_("Foreground content color to use on base color"),
        default="#1b1718ff",
    )
    info = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Info color"),
        help_text=_("For informative/helpful messages"),
        default="#00bafeff",
    )
    info_content = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Info content color"),
        help_text=_("Foreground content color to use on info color"),
        default="#042e49ff",
    )
    success = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Success color"),
        help_text=_("For success/safe messages"),
        default="#00d390ff",
    )
    success_content = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Success content color"),
        help_text=_("Foreground content color to use on success color"),
        default="#004c39ff",
    )
    warning = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Warning color"),
        help_text=_("For warning/caution messages"),
        default="#fcb700ff",
    )
    warning_content = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Warning content color"),
        help_text=_("Foreground content color to use on warning color"),
        default="#793205ff",
    )
    error = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Error color"),
        help_text=_("For error/danger/destructive messages"),
        default="#ff637dff",
    )
    error_content = DaisyUIColorField(
        format="hexa",
        verbose_name=_("Error content color"),
        help_text=_("Foreground content color to use on error color"),
        default="#4d0218ff",
    )

    panels = [
        DaisyUIColorPanel("primary"),
        DaisyUIColorPanel("primary_content"),
        DaisyUIColorPanel("secondary"),
        DaisyUIColorPanel("secondary_content"),
        DaisyUIColorPanel("accent"),
        DaisyUIColorPanel("accent_content"),
        DaisyUIColorPanel("neutral"),
        DaisyUIColorPanel("neutral_content"),
        DaisyUIColorPanel("base_100"),
        DaisyUIColorPanel("base_200"),
        DaisyUIColorPanel("base_300"),
        DaisyUIColorPanel("base_content"),
        DaisyUIColorPanel("info"),
        DaisyUIColorPanel("info_content"),
        DaisyUIColorPanel("success"),
        DaisyUIColorPanel("success_content"),
        DaisyUIColorPanel("warning"),
        DaisyUIColorPanel("warning_content"),
        DaisyUIColorPanel("error"),
        DaisyUIColorPanel("error_content"),
    ]

    def __str__(self):
        return f"{self.theme} {_('colors')}"
