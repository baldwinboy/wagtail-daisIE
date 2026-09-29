"""Models for notification integrations and MJML email templates."""

from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.models import LockableMixin, Orderable, PreviewableMixin, RevisionMixin

from ..base_blocks.audience import (
    get_audience_rule_choices,
    resolve_audience_queryset,
)
from ..base_blocks.design import PageDesignBlock
from .blocks import EmailVariableBlock
from .context import build_context
from .email_blocks import EmailContentBlock
from .email_rendering import (
    body_background_color,
    category_classes,
    font_urls,
    render_mjml,
    theme_attributes,
)
from .panels import EmailPlaceholdersHelpPanel
from .placeholders import render_placeholders


def audience_kind_choices():
    return Audience.Kind.choices


def campaign_status_choices():
    return EmailCampaign.Status.choices


def campaign_send_mode_choices():
    return [
        ("manual", _("Manual")),
        ("scheduled", _("Scheduled")),
    ]


def campaign_recurrence_choices():
    return EmailCampaign.Recurrence.choices


def campaign_log_status_choices():
    return CampaignRecipientLog.Status.choices


class EmailTemplate(
    LockableMixin,
    RevisionMixin,
    PreviewableMixin,
    ClusterableModel,
):
    """An MJML email document built from the package's design primitives."""

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
        from .preview import build_preview_context

        context = super().get_preview_context(request, mode_name)
        context["mjml_source"] = self.get_mjml(
            context=build_preview_context(
                request=request,
                subject=self.subject,
                preheader=self.preheader,
                content=str(self.content),
            )
        )
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
        from .rendering import render_email_template

        return render_email_template(
            self,
            payload=payload,
            recipient=recipient,
            request=request,
            site=site,
            from_email=from_email,
        )


class Audience(ClusterableModel):
    """A group of recipients for campaigns.

    A ``manual`` audience is a list of members; a ``rule`` audience uses the
    queryset declared by an entry in ``WAGTAIL_DAISIE_AUDIENCE_RULES``.
    """

    class Kind(models.TextChoices):
        MANUAL = "manual", _("Manual list")
        RULE = "rule", _("From audience rules")

    name = models.CharField(max_length=255, unique=True, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    kind = models.CharField(
        max_length=10,
        choices=audience_kind_choices,
        default=Kind.MANUAL,
        verbose_name=_("Type"),
    )
    rule_key = models.CharField(
        max_length=64,
        blank=True,
        choices=get_audience_rule_choices,
        verbose_name=_("Audience rule"),
        help_text=_("The settings audience rule to source users from."),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    panels = [
        FieldPanel("name"),
        FieldPanel("kind"),
        FieldPanel("rule_key"),
        FieldPanel("description"),
        FieldPanel("is_active"),
    ]

    class Meta:
        verbose_name = _("Audience")
        verbose_name_plural = _("Audiences")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_recipients(self):
        """Return the audience's recipients (users or email strings)."""
        if self.kind == self.Kind.RULE:
            queryset = resolve_audience_queryset(self.rule_key)
            return list(queryset) if queryset is not None else []
        recipients = []
        for member in self.members.filter(is_active=True).select_related("user"):
            if member.user_id:
                recipients.append(member.user)
            elif member.email:
                recipients.append(member.email)
        return recipients

    def get_emails(self):
        emails = []
        for recipient in self.get_recipients():
            email = (
                recipient
                if isinstance(recipient, str)
                else getattr(recipient, "email", "")
            )
            if email and email not in emails:
                emails.append(email)
        return emails


class AudienceMember(Orderable):
    """A member of a manual audience: an existing user or a bare email."""

    audience = ParentalKey(
        Audience,
        related_name="members",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("User"),
    )
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    name = models.CharField(max_length=255, blank=True, verbose_name=_("Name"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))

    panels = [
        FieldPanel("user"),
        FieldPanel("email"),
        FieldPanel("name"),
        FieldPanel("is_active"),
    ]

    class Meta:
        verbose_name = _("Audience member")
        verbose_name_plural = _("Audience members")
        ordering = ["sort_order"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(user__isnull=False) | ~models.Q(email=""),
                name="wagtail_daisIE.audience_member_target",
            ),
            models.UniqueConstraint(
                fields=["audience", "user"],
                condition=models.Q(user__isnull=False),
                name="wagtail_daisIE.unique_audience_user",
            ),
            models.UniqueConstraint(
                fields=["audience", "email"],
                condition=~models.Q(email=""),
                name="wagtail_daisIE.unique_audience_email",
            ),
        ]

    def __str__(self):
        return self.email or getattr(self.user, "email", "") or self.name


class EmailCampaign(
    LockableMixin,
    RevisionMixin,
    PreviewableMixin,
    ClusterableModel,
):
    """A scheduled (or manual) email sent to an audience."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        SCHEDULED = "scheduled", _("Scheduled")
        SENDING = "sending", _("Sending")
        SENT = "sent", _("Sent")
        FAILED = "failed", _("Failed")
        CANCELLED = "cancelled", _("Cancelled")

    class Recurrence(models.TextChoices):
        NONE = "none", _("One-off")
        DAILY = "daily", _("Daily")
        WEEKLY = "weekly", _("Weekly")
        MONTHLY = "monthly", _("Monthly")

    name = models.CharField(max_length=255, unique=True, verbose_name=_("Name"))
    template = models.ForeignKey(
        "EmailTemplate",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("Email template"),
    )
    audience = models.ForeignKey(
        Audience,
        on_delete=models.PROTECT,
        related_name="campaigns",
        verbose_name=_("Audience"),
    )
    status = models.CharField(
        max_length=16,
        choices=campaign_status_choices,
        default=Status.DRAFT,
        verbose_name=_("Status"),
    )
    send_mode = models.CharField(
        max_length=10,
        choices=campaign_send_mode_choices,
        default="manual",
        verbose_name=_("Send mode"),
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Scheduled at"),
        help_text=_("Used when the send mode is scheduled."),
    )
    recurrence = models.CharField(
        max_length=10,
        choices=campaign_recurrence_choices,
        default=Recurrence.NONE,
        verbose_name=_("Repeat"),
    )
    context = StreamField(
        [("variable", EmailVariableBlock())],
        blank=True,
        use_json_field=True,
        verbose_name=_("Variables"),
        help_text=_("Extra values exposed as {{ payload.<name> }}."),
    )
    last_sent_at = models.DateTimeField(null=True, blank=True, editable=False)
    sent_count = models.PositiveIntegerField(default=0, editable=False)
    failed_count = models.PositiveIntegerField(default=0, editable=False)

    revisions = GenericRelation(
        "wagtailcore.Revision",
        content_type_field="base_content_type",
        object_id_field="object_id",
        related_query_name="email_campaign",
        for_concrete_model=False,
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("template"),
        FieldPanel("audience"),
        FieldPanel("context"),
        MultiFieldPanel(
            [
                FieldPanel("send_mode"),
                FieldPanel("scheduled_at"),
                FieldPanel("recurrence"),
            ],
            heading=_("Schedule"),
        ),
        MultiFieldPanel(
            [FieldPanel("status")],
            heading=_("Status"),
            classname="collapsed",
        ),
    ]

    class Meta:
        verbose_name = _("Email campaign")
        verbose_name_plural = _("Email campaigns")
        ordering = ["-scheduled_at", "name"]

    def __str__(self):
        return self.name

    def get_payload(self):
        payload = {}
        for child in self.context or []:
            value = child.value if hasattr(child, "value") else child
            if not isinstance(value, dict):
                continue
            key = (value.get("key") or "").strip()
            if key:
                payload[key] = value.get("value", "")
        return payload

    def get_preview_template(self, request, mode_name):
        if self.template_id:
            return self.template.get_preview_template(request, mode_name)
        return EmailTemplate.get_preview_template(self, request, mode_name)

    def get_preview_context(self, request, mode_name):
        context = super().get_preview_context(request, mode_name)
        if self.template_id:
            from .preview import build_preview_context

            context["mjml_source"] = self.template.get_mjml(
                context=build_preview_context(
                    request=request,
                    subject=self.template.subject,
                    preheader=self.template.preheader,
                    content=str(self.template.content),
                    payload=self.get_payload(),
                )
            )
        return context


class CampaignRecipientLog(models.Model):
    """Per-recipient delivery record for a campaign (idempotency/dedupe)."""

    class Status(models.TextChoices):
        SENT = "sent", _("Sent")
        FAILED = "failed", _("Failed")
        SKIPPED = "skipped", _("Skipped")

    campaign = models.ForeignKey(
        EmailCampaign,
        on_delete=models.CASCADE,
        related_name="logs",
    )
    recipient_email = models.EmailField()
    status = models.CharField(
        max_length=10, choices=campaign_log_status_choices, default=Status.SENT
    )
    error = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Campaign recipient log")
        verbose_name_plural = _("Campaign recipient logs")
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "recipient_email"],
                name="wagtail_daisIE.unique_campaign_recipient",
            ),
        ]

    def __str__(self):
        return f"{self.campaign_id}: {self.recipient_email} ({self.status})"
