"""Models used by the test suite (no migrations; created via ``run_syncdb``)."""

from django.db import models

from wagtail_daisIE.detail_pages.models import ModelDetailPage, ModelDetailTemplate


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
