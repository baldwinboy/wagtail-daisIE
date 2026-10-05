"""Models for data-driven components."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField

from ..base_blocks.button import ButtonAppearanceBlock
from ..base_blocks.compact import DaisieStructBlock
from ..base_blocks.css import build_design_css
from ..base_blocks.design import TypographyDesignBlock
from ..dynamic.feeds import (
    gap_choices,
    layout_choices,
    row_mode_choices,
    toggle_choices,
)
from ..dynamic.panels import FeedContextModelHelpPanel
from ..dynamic.registry import get_context_model_choices, get_filter_choices
from .blocks_data import ITEM_BLOCKS


class FeedFilterBlock(DaisieStructBlock):
    """Select, label and style one of the model's declared filters."""

    key = blocks.ChoiceBlock(choices=get_filter_choices, label=_("Filter"))
    label = blocks.CharBlock(
        max_length=255,
        required=False,
        blank=True,
        label=_("Label override"),
        help_text=_("Shown instead of the filter's default label."),
    )
    collapsed = blocks.BooleanBlock(default=False, required=False)
    button_appearance = ButtonAppearanceBlock(
        required=False,
        label=_("Filter buttons"),
        help_text=_("Used for choice and boolean filters."),
    )
    input_design = TypographyDesignBlock(
        required=False,
        help_text=_("Used for date, range and search filters."),
    )
    label_design = TypographyDesignBlock(
        required=False,
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
    layout = models.CharField(
        max_length=8, choices=layout_choices, default="grid", verbose_name=_("Layout")
    )
    layout_columns = models.PositiveSmallIntegerField(
        default=3,
        verbose_name=_("Grid columns"),
        help_text=_("Used by the grid layout (1-6)."),
    )
    layout_gap = models.CharField(
        max_length=8, choices=gap_choices, default="gap-4", verbose_name=_("Gap")
    )
    row_mode = models.CharField(
        max_length=8,
        choices=row_mode_choices,
        default="wrap",
        verbose_name=_("Row behaviour"),
        help_text=_("Used by the row layout."),
    )
    allow_layout_toggle = models.BooleanField(
        default=False, verbose_name=_("Let visitors switch layout")
    )
    toggle_layouts = models.CharField(
        max_length=16,
        blank=True,
        default="grid_list",
        choices=toggle_choices,
        verbose_name=_("Toggle options"),
    )
    filters = StreamField(
        [("filter", FeedFilterBlock())],
        blank=True,
        use_json_field=True,
        verbose_name=_("Filters"),
        help_text=_("Choose and order the filters to show."),
        collapsed=True,
    )
    item = StreamField(
        ITEM_BLOCKS,
        blank=True,
        use_json_field=True,
        verbose_name=_("Item design"),
        collapsed=True,
    )
    submit_appearance = StreamField(
        [("appearance", ButtonAppearanceBlock())],
        blank=True,
        max_num=1,
        use_json_field=True,
        verbose_name=_("Submit / Load more button"),
        collapsed=True,
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("context_model"),
        FeedContextModelHelpPanel(),
        MultiFieldPanel(
            [
                FieldPanel("order_by"),
                FieldPanel("page_size"),
                FieldPanel("infinite"),
                FieldPanel("empty_message"),
                FieldPanel("submit_appearance"),
            ],
            heading=_("Display"),
            classname="collapsed",
        ),
        MultiFieldPanel(
            [
                FieldPanel("layout"),
                FieldPanel("layout_columns"),
                FieldPanel("layout_gap"),
                FieldPanel("row_mode"),
                FieldPanel("allow_layout_toggle"),
                FieldPanel("toggle_layouts"),
            ],
            heading=_("Layout"),
            classname="collapsed",
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
