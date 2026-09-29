"""Icon sources and favicon/PWA manifest settings."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.images import get_image_model_string

from ..icons.conf import get_iconify_config
from ..models.fields import DaisyUIColorField
from ..panels import DaisyUIColorPanel


def icon_provider_choices():
    return [
        ("iconify", _("Iconify")),
        ("font", _("Web font")),
        ("custom", _("Custom manifest")),
        ("wagtail", _("Wagtail admin icons")),
    ]


def favicon_display_choices():
    return DISPLAY_CHOICES


class DaisyUIIconSource(models.Model):
    """An icon source shown in the icon chooser.

    Each source maps to an :class:`~wagtail_daisIE.icons.providers.base.IconProvider`.
    Iconify collections, webfonts, custom manifests and the built-in Wagtail
    icon set can all be managed here.
    """

    PROVIDER_CHOICES = [
        ("iconify", _("Iconify")),
        ("font", _("Web font")),
        ("custom", _("Custom manifest")),
        ("wagtail", _("Wagtail admin icons")),
    ]

    label = models.CharField(
        max_length=255,
        verbose_name=_("Label"),
        help_text=_("Name shown in the icon picker."),
    )
    prefix = models.SlugField(
        max_length=64,
        unique=True,
        verbose_name=_("Prefix"),
        help_text=_(
            "Unique identifier used before the colon, e.g. 'mdi' in 'mdi:home'."
        ),
    )
    provider = models.CharField(
        max_length=16,
        choices=icon_provider_choices,
        default="iconify",
        verbose_name=_("Provider"),
    )
    enabled = models.BooleanField(
        default=True,
        verbose_name=_("Enabled"),
        help_text=_("Show this source in the icon picker."),
    )
    order = models.PositiveIntegerField(
        default=0, verbose_name=_("Order"), help_text=_("Lower numbers appear first.")
    )
    api_base = models.URLField(
        blank=True,
        verbose_name=_("Iconify API base URL"),
        help_text=_("Leave blank to use the configured default Iconify API."),
    )
    css_url = models.URLField(
        blank=True,
        verbose_name=_("Web font CSS URL"),
        help_text=_("Stylesheet that provides the icon font classes."),
    )
    css_class_prefix = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_("Class prefix"),
        help_text=_("Prefix added to the icon name, e.g. 'fa-solid fa-'."),
    )
    manifest_path = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Manifest path"),
        help_text=_("Filesystem path to an IconifyJSON or name-to-SVG manifest."),
    )
    search_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Searchable"),
        help_text=_("Allow searching this source in the picker."),
    )
    info = models.JSONField(
        default=dict,
        blank=True,
        editable=False,
        verbose_name=_("Cached metadata"),
    )

    panels = [
        HelpPanel(
            content=_(
                "<p>An icon source adds a family of icons to the icon picker. "
                "Iconify sources use a public or self-hosted Iconify API; "
                "web font sources rely on a stylesheet; custom sources read a "
                "local manifest; and the Wagtail source exposes the built-in "
                "admin icon set.</p>"
            )
        ),
        FieldPanel("label"),
        FieldPanel("prefix"),
        FieldPanel("provider"),
        FieldPanel("enabled"),
        FieldPanel("order"),
        MultiFieldPanel(
            [
                FieldPanel("api_base"),
            ],
            heading=_("Iconify"),
            classname="collapsed",
        ),
        MultiFieldPanel(
            [
                FieldPanel("css_url"),
                FieldPanel("css_class_prefix"),
            ],
            heading=_("Web font"),
            classname="collapsed",
        ),
        MultiFieldPanel(
            [
                FieldPanel("manifest_path"),
            ],
            heading=_("Custom manifest"),
            classname="collapsed",
        ),
        FieldPanel("search_enabled"),
    ]

    class Meta:
        ordering = ["order", "label"]
        verbose_name = _("DaisyUI Icon Source")
        verbose_name_plural = _("DaisyUI Icon Sources")

    def __str__(self):
        return self.label

    def to_provider(self):
        if self.provider == "iconify":
            from ..icons.providers.iconify import IconifyProvider

            provider = IconifyProvider(
                prefix=self.prefix,
                label=self.label,
                api_base=self.api_base or None,
                info=self.info,
            )
        elif self.provider == "font":
            from ..icons.providers.font import FontIconProvider

            provider = FontIconProvider(
                prefix=self.prefix,
                label=self.label,
                css_url=self.css_url,
                css_class_prefix=self.css_class_prefix,
            )
        elif self.provider == "custom":
            from ..icons.providers.custom import CustomIconProvider

            provider = CustomIconProvider(
                prefix=self.prefix,
                label=self.label,
                manifest_path=self.manifest_path,
            )
        elif self.provider == "wagtail":
            from ..icons.providers.wagtail import WagtailIconProvider

            provider = WagtailIconProvider()
        else:
            raise ValueError(f"Unknown icon provider: {self.provider!r}")

        provider.search_enabled = self.search_enabled
        return provider

    @classmethod
    def ensure_defaults(cls):
        """Create the default icon sources if none exist (idempotent)."""
        config = get_iconify_config()
        for index, collection in enumerate(config["collections"]):
            cls.objects.get_or_create(
                prefix=collection,
                defaults={
                    "label": collection,
                    "provider": "iconify",
                    "order": index,
                },
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
    theme_color = DaisyUIColorField(
        format="hexa",
        force_alpha=False,
        default="#FFFFFF",
        verbose_name=_("Theme colour"),
        help_text=_("Hex or hexa colour, e.g. #A1B2C3 or #A1B2C3FF."),
    )
    background_color = DaisyUIColorField(
        format="hexa",
        force_alpha=False,
        default="#FFFFFF",
        verbose_name=_("Background colour"),
        help_text=_("Hex or hexa colour, e.g. #A1B2C3 or #A1B2C3FF."),
    )
    display = models.CharField(
        max_length=16,
        blank=True,
        default="standalone",
        choices=favicon_display_choices,
        verbose_name=_("Display"),
    )

    panels = [
        FieldPanel("site"),
        MultiFieldPanel(
            [FieldPanel("image"), FieldPanel("app_name"), FieldPanel("short_name")],
            heading=_("Identity"),
            classname="collapsed",
        ),
        MultiFieldPanel(
            [
                DaisyUIColorPanel("theme_color"),
                DaisyUIColorPanel("background_color"),
                FieldPanel("display"),
            ],
            heading=_("PWA manifest"),
            classname="collapsed",
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
