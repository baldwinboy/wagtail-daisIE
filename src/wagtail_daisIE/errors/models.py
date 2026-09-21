"""Admin-designable error pages."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField

from ..blocks.content import ContentBlock


ERROR_STATUS_CHOICES = [
    (400, _("400 Bad request")),
    (401, _("401 Unauthorized")),
    (403, _("403 Forbidden")),
    (404, _("404 Not found")),
    (429, _("429 Too many requests")),
    (500, _("500 Server error")),
]


class ErrorPage(models.Model):
    """An admin-designed error page for a specific HTTP status code."""

    status_code = models.PositiveSmallIntegerField(
        unique=True,
        choices=ERROR_STATUS_CHOICES,
        verbose_name=_("Status code"),
        help_text=_("The HTTP status this page is shown for."),
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Title"),
        help_text=_("Heading shown above the page content."),
    )
    page_theme = models.ForeignKey(
        "wagtail_daisIE.DaisyUITheme",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Theme"),
        help_text=_("Theme used to style this error page. Falls back to the default."),
    )
    body = StreamField(
        ContentBlock(),
        blank=True,
        use_json_field=True,
        verbose_name=_("Body"),
        help_text=_("Content shown on the error page."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Only active pages are used; otherwise the default is shown."),
    )

    panels = [
        FieldPanel("status_code"),
        FieldPanel("title"),
        MultiFieldPanel(
            [FieldPanel("page_theme"), FieldPanel("is_active")],
            heading=_("Settings"),
        ),
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = _("Error page")
        verbose_name_plural = _("Error pages")
        ordering = ["status_code"]

    def __str__(self):
        return (
            f"{self.status_code} — {self.title}"
            if self.title
            else str(self.status_code)
        )
