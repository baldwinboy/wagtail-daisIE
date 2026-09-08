from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel

from ..icons.conf import get_iconify_config


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
        choices=PROVIDER_CHOICES,
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
