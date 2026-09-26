"""Favicon and PWA manifest settings, managed as a snippet."""

from __future__ import annotations

from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.images import get_image_model_string


hex_validator = RegexValidator(
    r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$",
    _("Enter a hex colour such as #A1B2C3."),
)

#: Sizes mirrored from the (unmaintained) wagtail-favicon project.
ICON_SIZES = ("192x192", "96x96", "32x32", "16x16")
APPLE_ICON_SIZES = (
    "180x180",
    "152x152",
    "144x144",
    "120x120",
    "114x114",
    "76x76",
    "72x72",
    "60x60",
    "57x57",
)
MANIFEST_ICONS = (
    ("36x36", "0.75"),
    ("48x48", "1.0"),
    ("72x72", "1.5"),
    ("96x96", "2.0"),
    ("144x144", "3.0"),
    ("192x192", "4.0"),
)

DISPLAY_CHOICES = [
    ("standalone", _("Standalone")),
    ("minimal-ui", _("Minimal UI")),
    ("fullscreen", _("Fullscreen")),
    ("browser", _("Browser")),
]


class DaisyUIFavicon(models.Model):
    """Favicon and web-app manifest settings, editable under the Design menu."""

    site = models.ForeignKey(
        "wagtailcore.Site",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Site"),
        help_text=_("Leave blank to use this favicon as the default for all sites."),
    )
    image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Favicon image"),
        help_text=_("A square, transparent PNG at least 1024x1024 works best."),
    )
    app_name = models.CharField(max_length=128, blank=True, verbose_name=_("App name"))
    short_name = models.CharField(
        max_length=64, blank=True, verbose_name=_("Short name")
    )
    theme_color = models.CharField(
        max_length=7,
        blank=True,
        validators=[hex_validator],
        verbose_name=_("Theme colour"),
    )
    background_color = models.CharField(
        max_length=7,
        blank=True,
        validators=[hex_validator],
        verbose_name=_("Background colour"),
    )
    display = models.CharField(
        max_length=16,
        blank=True,
        default="standalone",
        choices=DISPLAY_CHOICES,
        verbose_name=_("Display"),
    )

    panels = [
        FieldPanel("site"),
        MultiFieldPanel(
            [FieldPanel("image"), FieldPanel("app_name"), FieldPanel("short_name")],
            heading=_("Identity"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("theme_color"),
                FieldPanel("background_color"),
                FieldPanel("display"),
            ],
            heading=_("PWA manifest"),
        ),
    ]

    class Meta:
        verbose_name = _("Favicon")
        verbose_name_plural = _("Favicons")
        constraints = [
            models.UniqueConstraint(
                fields=["site"],
                condition=models.Q(site__isnull=False),
                name="wagtail_daisIE_unique_favicon_site",
            ),
            models.UniqueConstraint(
                fields=["site"],
                condition=models.Q(site__isnull=True),
                name="wagtail_daisIE_unique_favicon_default",
            ),
        ]

    def __str__(self):
        return str(self.site or _("All sites"))

    # --- resolution (lazy; never at import) ---------------------------------

    @classmethod
    def for_request(cls, request):
        """Return the site-specific favicon, falling back to the global one."""
        from wagtail.models import Site

        site = Site.find_for_request(request) if request is not None else None
        if site is not None:
            match = cls.objects.filter(site=site).first()
            if match is not None:
                return match
        return cls.objects.filter(site__isnull=True).first()

    @classmethod
    def get_default(cls):
        return cls.objects.filter(site__isnull=True).first()

    # --- renditions ---------------------------------------------------------

    def rendition_url(self, size):
        """Return the rendition URL for ``size`` (``WxH``), or an empty string."""
        if not self.image:
            return ""
        return self.image.get_rendition(f"fill-{size}").url

    def icons(self):
        return [{"size": size, "url": self.rendition_url(size)} for size in ICON_SIZES]

    def apple_icons(self):
        return [
            {"size": size, "url": self.rendition_url(size)} for size in APPLE_ICON_SIZES
        ]

    def tile_image(self):
        return self.rendition_url("144x144")

    # --- manifest -----------------------------------------------------------

    def manifest(self):
        """Return the web-app manifest as a JSON-serialisable dict."""
        data = {
            "icons": [
                {
                    "src": self.rendition_url(size),
                    "sizes": size,
                    "type": "image/png",
                    "density": density,
                }
                for size, density in MANIFEST_ICONS
            ],
        }
        if self.app_name:
            data["name"] = self.app_name
        if self.short_name:
            data["short_name"] = self.short_name
        if self.theme_color:
            data["theme_color"] = self.theme_color
        if self.background_color:
            data["background_color"] = self.background_color
        if self.display:
            data["display"] = self.display
        return data
