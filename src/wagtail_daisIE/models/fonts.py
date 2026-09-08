from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.models import (
    ClusterableModel,
    Orderable,
)

from wagtail_daisIE.panels import (
    DaisyUISizePanel,
)

from ..choices import FONT_FAMILY_ROLE_CHOICES, GENERIC_FONT_FAMILY_CHOICES
from .fields import DaisyUISizeField


class DaisyUIThemeFontCDN(Orderable):
    theme = ParentalKey(
        "wagtail_daisIE.DaisyUITheme",
        on_delete=models.CASCADE,
        related_name="font_cdns",
    )
    url = models.URLField(
        verbose_name=_("Font CDN URL"),
        help_text=_("Full URL to a font stylesheet (e.g. Google Fonts link tag href)"),
    )
    label = models.CharField(
        max_length=255,
        verbose_name=_("Label"),
        help_text=_("Optional label to identify this CDN link"),
        blank=True,
    )

    panels = [
        FieldPanel("url"),
        FieldPanel("label"),
    ]

    def __str__(self):
        return self.label or self.url


class DaisyUIThemeFonts(ClusterableModel, Orderable):
    theme = ParentalKey(
        "wagtail_daisIE.DaisyUITheme",
        on_delete=models.CASCADE,
        related_name="fonts",
    )
    base_font_size = DaisyUISizeField(
        verbose_name=_("Base font size"),
        help_text=_("Base font size for body text"),
        default="1rem",
    )
    line_height = models.FloatField(
        verbose_name=_("Line height"),
        help_text=_("Line height multiplier for body text"),
        default=1.5,
    )

    panels = [
        InlinePanel("font_families", label=_("Font families"), classname="collapsed"),
        DaisyUISizePanel("base_font_size"),
        FieldPanel("line_height"),
    ]

    def __str__(self):
        return f"{self.theme} {_('fonts')}"


class DaisyUIThemeFontFamily(ClusterableModel, Orderable):
    fonts = ParentalKey(
        "wagtail_daisIE.DaisyUIThemeFonts",
        on_delete=models.CASCADE,
        related_name="font_families",
    )
    role = models.CharField(
        max_length=16,
        choices=FONT_FAMILY_ROLE_CHOICES,
        default="body",
        verbose_name=_("Role"),
        help_text=_(
            "The font family is used for what? "
            "Headings, body text, code, or a custom stack."
        ),
    )
    name = models.SlugField(
        max_length=255,
        blank=True,
        verbose_name=_("Name"),
        help_text=_(
            "Identifier for custom fonts, used in CSS variables. "
            "E.g. 'display' becomes --font-display."
            "Required for custom fonts."
        ),
    )
    font_family = models.CharField(
        max_length=255,
        verbose_name=_("Font family name"),
        help_text=_("Primary font family name, e.g. Inter."),
        default="Inter",
    )
    generic_font_family = models.CharField(
        max_length=255,
        verbose_name=_("Generic font family"),
        help_text=_(
            "Browser-provided font used as the last resort "
            "if none of the fonts above are available."
        ),
        default="sans-serif",
        choices=GENERIC_FONT_FAMILY_CHOICES,
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("font_family"),
        FieldPanel("generic_font_family"),
        InlinePanel(
            "fallbacks", label=_("Fallback font families"), classname="collapsed"
        ),
    ]

    class Meta:
        constraints = [
            # Ensure that only one font family is set as the default
            UniqueConstraint(
                fields=["fonts", "role"],
                condition=Q(role__in=["heading", "body", "subheading", "code"]),
                name="wagtail_daisIE.unique_font_family_role",
            ),
            # Ensure that each custom font has a unique name
            UniqueConstraint(
                fields=["fonts", "name"],
                condition=Q(role="custom"),
                name="wagtail_daisIE.unique_font_family_name",
            ),
            # Ensure that each custom font has a name
            CheckConstraint(
                condition=~Q(role="custom") | ~Q(name=""),
                name="wagtail_daisIE.check_font_family_name",
            ),
        ]

    def __str__(self):
        return self.name if self.role == "custom" else self.role

    def clean(self):
        super().clean()
        # Custom fonts must have a name
        if self.role == "custom":
            if self.name is None:
                raise ValidationError(
                    _("Custom font families must have a name."),
                    code="wagtail_daisIE.custom_font_family_missing_name",
                )
            return

        # Headings, body, subheading, and code fonts must have a unique role
        duplicate_role_exists = (
            type(self)
            .objects.filter(role=self.role, fonts=self.fonts)
            .exclude(pk=self.pk)
            .exists()
        )

        if duplicate_role_exists:
            raise ValidationError(
                _(f"A {self.role} font already exists for this theme."),
                code="wagtail_daisIE.duplicate_font_family_role",
            )

    @property
    def css_value(self) -> str:
        fallback_css_values = [fb.css_value for fb in self.fallbacks.all()]
        parts = [
            f"'{self.font_family}'",
            *fallback_css_values,
            self.generic_font_family,
        ]
        return ", ".join(parts)


class DaisyUIThemeFontFallback(Orderable):
    font_family = ParentalKey(
        "wagtail_daisIE.DaisyUIThemeFontFamily",
        on_delete=models.CASCADE,
        related_name="fallbacks",
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Font family name"),
        help_text=_("Font family name for the fallback font, e.g. Roboto."),
    )

    panels = [
        FieldPanel("name"),
    ]

    def __str__(self):
        return self.font_family

    @property
    def css_value(self) -> str:
        return f"'{self.font_family}'"
