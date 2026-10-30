"""Admin-designed content that can be referenced from anywhere in the site."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField

from ..blocks.content_blocks import REUSABLE_CONTENT_BLOCKS


class ReusableBlock(ClusterableModel):
    """A saved, designed section of page content, referenced by a block.

    Editing an entry updates every page, form, menu or feed item card that
    imports it (a live reference). Its content excludes the reusable chooser, so
    entries cannot nest or recurse.
    """

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Name"),
        help_text=_('A unique name, e.g. "Homepage promo".'),
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Description"),
        help_text=_("An optional note to help other editors."),
    )
    content = StreamField(
        REUSABLE_CONTENT_BLOCKS,
        blank=True,
        use_json_field=True,
        verbose_name=_("Content"),
        help_text=_("Design the content to reuse. Importing it renders this."),
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("description"),
        FieldPanel("content"),
    ]

    class Meta:
        verbose_name = _("Reusable block")
        verbose_name_plural = _("Reusable blocks")
        ordering = ["name"]

    def clean(self):
        super().clean()
        from ..base_blocks.visibility import validate_visibility_stream

        validate_visibility_stream(self.content, _("Reusable block content"))

    def __str__(self):
        return self.name
