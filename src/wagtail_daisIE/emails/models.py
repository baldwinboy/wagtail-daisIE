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
from ..notifications.context import build_context
from ..notifications.panels import EmailPlaceholdersHelpPanel
from ..notifications.placeholders import render_placeholders
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
    template_key = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Template key"),
        help_text=_(
            "Optional stable key used to bind this template to a bridge or "
            "integration (e.g. an allauth email prefix)."
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
        EmailPlaceholdersHelpPanel(),
        FieldPanel("name"),
        FieldPanel("template_key"),
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
        context["mjml_source"] = self.get_mjml(context=build_context(request=request))
        return context

    def get_design_value(self):
        return self.design[0].value if self.design else None

    def get_mjml_context(self, *, payload=None, recipient=None, context=None):
        render_context = (
            dict(context)
            if context is not None
            else build_context(payload=payload, recipient=recipient)
        )
        theme = self.get_theme()
        render_context.update(
            {
                "email_theme": theme,
                "content": self.content,
                "subject": render_placeholders(
                    self.subject,
                    render_context,
                    escape_literals=False,
                    escape_values=False,
                ),
                "preheader": render_placeholders(
                    self.preheader,
                    render_context,
                    escape_literals=False,
                    escape_values=False,
                ),
                "theme_attributes": theme_attributes(theme),
                "font_urls": font_urls(theme),
                "mj_classes": category_classes(self.get_design_value(), theme),
                "body_background_color": body_background_color(theme),
            }
        )
        return render_context

    def get_mjml(self, *, payload=None, recipient=None, context=None):
        """Return the raw MJML document (not yet compiled to HTML)."""
        return render_mjml(
            self,
            payload=payload,
            recipient=recipient,
            context=context,
        )

    def render(
        self,
        *,
        payload=None,
        recipient=None,
        request=None,
        site=None,
        from_email=None,
    ):
        """Render to a subject/HTML/text bundle for the given context."""
        from ..notifications.rendering import render_email_template

        return render_email_template(
            self,
            payload=payload,
            recipient=recipient,
            request=request,
            site=site,
            from_email=from_email,
        )
