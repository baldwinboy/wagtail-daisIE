"""MJML email template model.

``EmailTemplate`` lets content authors build raw MJML email documents with the
same design primitives the package uses for pages. The MJML source is produced
by :meth:`EmailTemplate.get_mjml`; the admin preview compiles it through the
``{% mjml %}`` template tag.
"""

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import LockableMixin, PreviewableMixin, RevisionMixin

from ..base_blocks.design import PageDesignBlock
from .blocks import EmailContentBlock
from .rendering import (
    body_background_color,
    category_classes,
    font_urls,
    render_mjml,
    theme_attributes,
)


class EmailTemplate(
    LockableMixin,
    RevisionMixin,
    PreviewableMixin,
    ClusterableModel,
):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Name"),
        help_text=_(
            'A unique name used to identify this template, e.g. "Welcome email".'
        ),
    )
    subject = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Subject"),
        help_text=_("Stored as the MJML title, e.g. for the email subject line."),
    )
    preheader = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Preheader"),
        help_text=_("Short preview text shown by email clients after the subject."),
    )
    email_theme = models.ForeignKey(
        "wagtail_daisIE.DaisyUITheme",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Email theme"),
        help_text=_("Theme applied to this email. Falls back to the default theme."),
    )
    design = StreamField(
        [("defaults", PageDesignBlock())],
        blank=True,
        max_num=1,
        use_json_field=True,
        verbose_name=_("Default design"),
        help_text=_(
            "Default container, text, button and media styles applied to every "
            "block in this email. Per-block settings are applied on top."
        ),
    )
    content = StreamField(
        EmailContentBlock(),
        blank=True,
        use_json_field=True,
        verbose_name=_("Email content"),
        help_text=_("Add MJML components to build the email body."),
    )

    revisions = GenericRelation(
        "wagtailcore.Revision",
        content_type_field="base_content_type",
        object_id_field="object_id",
        related_query_name="email_template",
        for_concrete_model=False,
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("subject"),
        FieldPanel("preheader"),
        FieldPanel("content"),
    ]

    styling_panels = [
        FieldPanel("email_theme"),
        FieldPanel("design"),
    ]

    class Meta:
        verbose_name = _("Email template")
        verbose_name_plural = _("Email templates")

    def __str__(self):
        return self.name

    def get_theme(self):
        """Return this email's theme, falling back to the default theme."""
        if self.email_theme_id:
            return self.email_theme
        from ..models import DaisyUITheme

        return DaisyUITheme.objects.filter(default=True).first()

    def get_preview_template(self, request, mode_name):
        return "wagtail_daisIE/emails/blocks/preview.html"

    def get_preview_context(self, request, mode_name):
        context = super().get_preview_context(request, mode_name)
        context["mjml_source"] = self.get_mjml()
        return context

    def get_design_value(self):
        return self.design[0].value if self.design else None

    def get_mjml_context(self):
        theme = self.get_theme()
        return {
            "email_theme": theme,
            "content": self.content,
            "subject": self.subject,
            "preheader": self.preheader,
            "theme_attributes": theme_attributes(theme),
            "font_urls": font_urls(theme),
            "mj_classes": category_classes(self.get_design_value(), theme),
            "body_background_color": body_background_color(theme),
        }

    def get_mjml(self):
        """Return the raw MJML document (not yet compiled to HTML)."""
        return render_mjml(self)
