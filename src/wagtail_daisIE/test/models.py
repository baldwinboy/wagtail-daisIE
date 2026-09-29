"""Models used by the test suite (no migrations; created via ``run_syncdb``)."""

from django.db import models

from wagtail_daisIE.detail_pages.models import ModelDetailPage, ModelDetailTemplate
from wagtail_daisIE.pages import StyledPageMixin


class Widget(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    is_available = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class WidgetDetailTemplate(ModelDetailTemplate):
    template = "wagtail_daisIE/test/detail.html"


class WidgetDetailPage(ModelDetailPage):
    template = "wagtail_daisIE/test/detail.html"


class WidgetIndexPage(StyledPageMixin):
    template = "wagtail_daisIE/test/detail.html"


class ApprovalTarget(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ApprovalSource(models.Model):
    name = models.CharField(max_length=255)
    is_approved = models.BooleanField(default=False)
    converted = models.ForeignKey(
        ApprovalTarget,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
