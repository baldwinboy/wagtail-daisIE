from colorfield.fields import ColorField
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.models import (
    DraftStateMixin,
    LockableMixin,
    PreviewableMixin,
    RevisionMixin,
    WorkflowMixin,
)

from .form_fields import DaisyUISizeFormField
from .panels import DaisyUIColorPanel, DaisyUISizePanel
from .widgets import DaisyUISize


class DaisyUIColorSchemeChoices(models.TextChoices):
    NORMAL = "normal", _("Normal")
    LIGHT = "light", _("Light")
    DARK = "dark", _("Dark")


class DaisyUISizeField(models.CharField):
    description = _("A CSS size (e.g. 10px, 2.5em)")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 20)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if kwargs.get("max_length") == 20:
            kwargs.pop("max_length", None)
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        """Convert the database string to a Python DaisyUISize object."""
        if value is None:
            return value
        return self.to_python(value)

    def to_python(self, value):
        return DaisyUISize.from_value(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if isinstance(value, DaisyUISize):
            return str(value)
        return value

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def formfield(self, **kwargs):
        defaults = {
            "form_class": DaisyUISizeFormField,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)


class DaisyUITheme(
    WorkflowMixin,
    DraftStateMixin,
    RevisionMixin,
    LockableMixin,
    PreviewableMixin,
    ClusterableModel,
):
    name = models.CharField(
        max_length=255, unique=True, primary_key=True, verbose_name=_("Name")
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
    workflow_states = GenericRelation(
        "wagtailcore.WorkflowState",
        content_type_field="base_content_type",
        object_id_field="object_id",
        related_query_name="daisyui_theme",
        for_concrete_model=False,
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("default"),
        FieldPanel("prefers_dark"),
        FieldPanel("color_scheme"),
        InlinePanel("colors", min_num=1, max_num=1, heading=_("Colors")),
        InlinePanel("radii", min_num=1, max_num=1, heading=_("Border radii")),
        InlinePanel("sizes", min_num=1, max_num=1, heading=_("Sizes")),
        InlinePanel("effects", min_num=1, max_num=1, heading=_("Effects")),
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


class DaisyUIThemePageMixin(models.Model):
    daisyui_theme = models.ForeignKey(
        DaisyUITheme,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("DaisyUI Theme"),
        help_text=_("Select a DaisyUI theme to style this page"),
    )

    class Meta:
        abstract = True

    def get_daisyui_theme(self):
        return self.daisyui_theme or DaisyUITheme.objects.filter(default=True).first()

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["daisyui_theme"] = self.get_daisyui_theme()
        return context


class DaisyUIThemeColors(models.Model):
    theme = ParentalKey(
        DaisyUITheme,
        on_delete=models.CASCADE,
        unique=True,
        related_name="colors",
    )
    primary = ColorField(
        format="hexa",
        verbose_name=_("Primary theme color"),
        help_text=_("The main color of your theme"),
        default="#422ad5ff",
    )
    primary_content = ColorField(
        format="hexa",
        verbose_name=_("Primary theme content color"),
        help_text=_("Foreground content color to use on primary color"),
        default="#e0e7ffff",
    )
    secondary = ColorField(
        format="hexa",
        verbose_name=_("Secondary theme color"),
        help_text=_("The secondary color of your theme"),
        default="#f43098ff",
    )
    secondary_content = ColorField(
        format="hexa",
        verbose_name=_("Secondary theme content color"),
        help_text=_("Foreground content color to use on secondary color"),
        default="#f9e4f0ff",
    )
    accent = ColorField(
        format="hexa",
        verbose_name=_("Accent theme color"),
        help_text=_("The accent color of your theme"),
        default="#00d3bbff",
    )
    accent_content = ColorField(
        format="hexa",
        verbose_name=_("Accent theme content color"),
        help_text=_("Foreground content color to use on accent color"),
        default="#084d49ff",
    )
    neutral = ColorField(
        format="hexa",
        verbose_name=_("Neutral dark color"),
        help_text=_("For not-saturated parts of UI"),
        default="#0b0809ff",
    )
    neutral_content = ColorField(
        format="hexa",
        verbose_name=_("Neutral dark content color"),
        help_text=_("Foreground content color to use on neutral color"),
        default="#e7e3e4ff",
    )
    base_100 = ColorField(
        format="hexa",
        verbose_name=_("Base surface color of page"),
        help_text=_("Used for blank backgrounds"),
        default="#ffffffff",
    )
    base_200 = ColorField(
        format="hexa",
        verbose_name=_("Base color, darker shade"),
        help_text=_("To create elevations"),
        default="##f8f8f8ff",
    )
    base_300 = ColorField(
        format="hexa",
        verbose_name=_("Base color, even darker shade"),
        help_text=_("To create elevations"),
        default="#eeeeeeff",
    )
    base_content = ColorField(
        format="hexa",
        verbose_name=_("Base content color"),
        help_text=_("Foreground content color to use on base color"),
        default="#1b1718ff",
    )
    info = ColorField(
        format="hexa",
        verbose_name=_("Info color"),
        help_text=_("For informative/helpful messages"),
        default="#00bafeff",
    )
    info_content = ColorField(
        format="hexa",
        verbose_name=_("Info content color"),
        help_text=_("Foreground content color to use on info color"),
        default="#042e49ff",
    )
    success = ColorField(
        format="hexa",
        verbose_name=_("Success color"),
        help_text=_("For success/safe messages"),
        default="#00d390ff",
    )
    success_content = ColorField(
        format="hexa",
        verbose_name=_("Success content color"),
        help_text=_("Foreground content color to use on success color"),
        default="#004c39ff",
    )
    warning = ColorField(
        format="hexa",
        verbose_name=_("Warning color"),
        help_text=_("For warning/caution messages"),
        default="#fcb700ff",
    )
    warning_content = ColorField(
        format="hexa",
        verbose_name=_("Warning content color"),
        help_text=_("Foreground content color to use on warning color"),
        default="#793205ff",
    )
    error = ColorField(
        format="hexa",
        verbose_name=_("Error color"),
        help_text=_("For error/danger/destructive messages"),
        default="#ff637dff",
    )
    error_content = ColorField(
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

    class Meta:
        verbose_name = _("DaisyUI Theme Colors")
        verbose_name_plural = _("DaisyUI Theme Colors")

    def __str__(self):
        return f"{self.theme} {_('colors')}"


class DaisyUIThemeRadii(models.Model):
    theme = ParentalKey(
        DaisyUITheme,
        on_delete=models.CASCADE,
        unique=True,
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

    class Meta:
        verbose_name = _("DaisyUI Theme Border Radii")
        verbose_name_plural = _("DaisyUI Theme Border Radii")

    def __str__(self):
        return f"{self.theme} {_('border radii')}"


class DaisyUIThemeSizes(models.Model):
    theme = ParentalKey(
        DaisyUITheme,
        on_delete=models.CASCADE,
        unique=True,
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

    class Meta:
        verbose_name = _("DaisyUI Theme Sizes")
        verbose_name_plural = _("DaisyUI Theme Sizes")

    def __str__(self):
        return f"{self.theme} {_('sizes')}"


class DaisyUIThemeEffects(models.Model):
    theme = ParentalKey(
        DaisyUITheme,
        on_delete=models.CASCADE,
        unique=True,
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

    class Meta:
        verbose_name = _("DaisyUI Theme Effects")
        verbose_name_plural = _("DaisyUI Theme Effects")

    def __str__(self):
        return f"{self.theme} {_('effects')}"
