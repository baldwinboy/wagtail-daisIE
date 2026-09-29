"""Models for binding allauth emails to DaisyUI email templates."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel

from .catalogue import get_allauth_email_choices, get_allauth_emails


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
        "wagtail_daisIE_notifications.EmailTemplate",
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
