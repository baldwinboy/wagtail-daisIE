"""Models for notification integrations."""

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
from .allauth_catalogue import get_allauth_email_choices, get_allauth_emails
from .blocks import EmailVariableBlock


class AllauthEmailOverride(models.Model):
    """Bind an allauth email prefix to a DaisyUI email template."""

    template_prefix = models.CharField(
        max_length=255,
        unique=True,
        choices=get_allauth_email_choices,
        verbose_name=_("Allauth email"),
        help_text=_("The allauth email event to override."),
    )
    email_template = models.ForeignKey(
        "wagtail_daisIE.EmailTemplate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Email template"),
        help_text=_("Leave empty to use allauth's default templates."),
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name=_("Active"),
        help_text=_("Only active overrides are used."),
    )

    panels = [
        FieldPanel("template_prefix"),
        FieldPanel("email_template"),
        FieldPanel("is_active"),
    ]

    class Meta:
        verbose_name = _("Allauth email override")
        verbose_name_plural = _("Allauth email overrides")
        ordering = ["template_prefix"]

    def __str__(self):
        try:
            label = self.get_template_prefix_display()
        except Exception:  # pragma: no cover - defensive
            label = self.template_prefix
        return str(label or self.template_prefix)

    @classmethod
    def ensure_defaults(cls):
        """Create a row for every discovered allauth email prefix."""
        created = 0
        for email in get_allauth_emails():
            _row, was_created = cls.objects.get_or_create(template_prefix=email.prefix)
            created += int(was_created)
        return created

    @classmethod
    def get_active(cls, template_prefix):
        return (
            cls.objects.select_related("email_template")
            .filter(
                template_prefix=template_prefix,
                is_active=True,
                email_template__isnull=False,
            )
            .first()
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
        choices=Kind.choices,
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
        "wagtail_daisIE.EmailTemplate",
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
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_("Status"),
    )
    send_mode = models.CharField(
        max_length=10,
        choices=[("manual", _("Manual")), ("scheduled", _("Scheduled"))],
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
        choices=Recurrence.choices,
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
        from ..emails.models import EmailTemplate

        return EmailTemplate.get_preview_template(self, request, mode_name)

    def get_preview_context(self, request, mode_name):
        context = super().get_preview_context(request, mode_name)
        if self.template_id:
            from .context import build_context

            context["mjml_source"] = self.template.get_mjml(
                context=build_context(request=request, payload=self.get_payload())
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
        max_length=10, choices=Status.choices, default=Status.SENT
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
