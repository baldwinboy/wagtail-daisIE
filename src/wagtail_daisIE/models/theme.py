from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, HelpPanel, InlinePanel
from wagtail.models import (
    LockableMixin,
    PreviewableMixin,
    RevisionMixin,
)

from .fields import DaisyUIColorSchemeChoices


class DaisyUITheme(
    LockableMixin,
    RevisionMixin,
    PreviewableMixin,
    ClusterableModel,
):
    name = models.CharField(
        max_length=255,
        primary_key=True,
        serialize=False,
        unique=True,
        verbose_name=_("Name"),
    )
    default = models.BooleanField(
        default=False,
        verbose_name=_("Set as default"),
        help_text=_("Is this the default theme?"),
    )
    prefers_dark = models.BooleanField(
        default=False,
        verbose_name=_("Set as default dark theme"),
        help_text=_("Is this the default dark theme?"),
    )
    color_scheme = models.CharField(
        max_length=128,
        choices=DaisyUIColorSchemeChoices.choices,
        default=DaisyUIColorSchemeChoices.LIGHT,
        verbose_name=_("Color scheme"),
        help_text=_("This theme will be applied to browsers with this color scheme"),
    )
    revisions = GenericRelation(
        "wagtailcore.Revision", related_query_name="daisyui_theme"
    )

    panels = [
        HelpPanel(template="wagtail_daisIE/admin/theme_help.html"),
        FieldPanel("name"),
        FieldPanel("default"),
        FieldPanel("prefers_dark"),
        FieldPanel("color_scheme"),
        InlinePanel(
            "colors", min_num=1, max_num=1, heading=_("Colors"), classname="collapsed"
        ),
        InlinePanel(
            "radii",
            min_num=1,
            max_num=1,
            heading=_("Border radii"),
            classname="collapsed",
        ),
        InlinePanel(
            "sizes", min_num=1, max_num=1, heading=_("Sizes"), classname="collapsed"
        ),
        InlinePanel(
            "effects", min_num=1, max_num=1, heading=_("Effects"), classname="collapsed"
        ),
        InlinePanel(
            "background",
            min_num=1,
            max_num=1,
            heading=_("Background"),
            classname="collapsed",
        ),
        InlinePanel("fonts", heading=_("Fonts"), max_num=1, classname="collapsed"),
        InlinePanel("font_cdns", heading=_("Font CDNs"), classname="collapsed"),
    ]

    class Meta:
        verbose_name = _("DaisyUI Theme")
        verbose_name_plural = _("DaisyUI Themes")
        constraints = [
            # Ensure that only one theme is set as default
            models.UniqueConstraint(
                fields=["default"],
                condition=models.Q(default=True),
                name="wagtail_daisIE.unique_default_theme",
            ),
            # Ensure that only one theme is set as default dark theme
            models.UniqueConstraint(
                fields=["prefers_dark"],
                condition=models.Q(prefers_dark=True),
                name="wagtail_daisIE.unique_default_dark_theme",
            ),
        ]

    def __str__(self):
        return self.name

    def get_preview_template(self, request, mode_name):
        return "wagtail_daisIE/previews/theme.html"
