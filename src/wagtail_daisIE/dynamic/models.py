"""Models for data-driven components."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField

from ..base_blocks.button import ButtonAppearanceBlock
from ..base_blocks.css import build_design_css
from ..base_blocks.design import TypographyDesignBlock
from .blocks_data import ITEM_BLOCKS
from .registry import get_context_model_choices, get_filter_choices


class FeedFilterBlock(blocks.StructBlock):
    """Select, label and style one of the model's declared filters."""

    key = blocks.ChoiceBlock(choices=get_filter_choices, label=_("Filter"))
    label = blocks.CharBlock(
        max_length=255,
        required=False,
        blank=True,
        label=_("Label override"),
        help_text=_("Shown instead of the filter's default label."),
    )
    collapsed = blocks.BooleanBlock(default=False, required=False, label=_("Collapsed"))
    button_appearance = ButtonAppearanceBlock(
        required=False,
        label=_("Filter buttons"),
        help_text=_("Used for choice and boolean filters."),
    )
    input_design = TypographyDesignBlock(
        required=False,
        label=_("Input design"),
        help_text=_("Used for date, range and search filters."),
    )
    label_design = TypographyDesignBlock(
        required=False,
        label=_("Label design"),
    )

    class Meta:
        icon = "funnel"
        label = _("Filter")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "key",
                "label",
                "collapsed",
                "button_appearance",
                "input_design",
                "label_design",
            ],
            heading=_("Filter"),
        )


class Feed(ClusterableModel):
    """An admin-designed, filterable list of a context model."""

    name = models.CharField(max_length=255, unique=True, verbose_name=_("Name"))
    context_model = models.CharField(
        max_length=64,
        choices=get_context_model_choices,
        verbose_name=_("Model"),
    )
    order_by = models.CharField(
        max_length=128,
        blank=True,
        default="-pk",
        verbose_name=_("Order by"),
        help_text=_("A model field, optionally prefixed with '-'."),
    )
    page_size = models.PositiveIntegerField(default=9, verbose_name=_("Items per page"))
    infinite = models.BooleanField(
        default=False,
        verbose_name=_("Infinite scroll"),
        help_text=_(
            "Load more as the visitor scrolls. Otherwise a Load more button is shown."
        ),
    )
    empty_message = models.CharField(
        max_length=255,
        blank=True,
        default="Nothing to show yet.",
        verbose_name=_("Empty message"),
    )
    filters = StreamField(
        [("filter", FeedFilterBlock())],
        blank=True,
        use_json_field=True,
        verbose_name=_("Filters"),
        help_text=_("Choose and order the filters to show."),
    )
    item = StreamField(
        ITEM_BLOCKS,
        blank=True,
        use_json_field=True,
        verbose_name=_("Item design"),
    )
    submit_appearance = StreamField(
        [("appearance", ButtonAppearanceBlock())],
        blank=True,
        max_num=1,
        use_json_field=True,
        verbose_name=_("Submit / Load more button"),
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("context_model"),
        MultiFieldPanel(
            [
                FieldPanel("order_by"),
                FieldPanel("page_size"),
                FieldPanel("infinite"),
                FieldPanel("empty_message"),
                FieldPanel("submit_appearance"),
            ],
            heading=_("Display"),
        ),
        FieldPanel("filters"),
        FieldPanel("item"),
    ]

    class Meta:
        verbose_name = _("Feed")
        verbose_name_plural = _("Feeds")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_submit_css(self):
        value = self.submit_appearance[0].value if self.submit_appearance else None
        return build_design_css({"button_appearance": value}) or "btn"
