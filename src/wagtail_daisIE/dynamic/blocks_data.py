"""Data-driven components: feeds, action buttons and calendars."""

from __future__ import annotations

from collections import OrderedDict
from datetime import date

from django.conf import settings
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.snippets.blocks import SnippetChooserBlock

from ..base_blocks import ThemedBlock
from ..blocks.content_blocks import PAGE_CONTENT_BLOCKS
from .actions import get_action_choices
from .feeds import (
    base_context as _base_context,
)
from .feeds import (
    base_queryset as _base_queryset,
)
from .feeds import (
    render_feed,
)
from .feeds import (
    render_stream as _render_stream,
)
from .feeds import (
    request_and_page as _request_and_page,
)
from .registry import get_context_model, get_context_model_choices


class ActionButtonBlock(ThemedBlock):
    """A button that posts to a developer-defined action."""

    action = blocks.ChoiceBlock(choices=get_action_choices, label=_("Action"))
    label = blocks.CharBlock(max_length=64, default="Go", label=_("Label"))
    button_class = blocks.CharBlock(
        max_length=128, default="btn btn-primary", label=_("Button classes")
    )
    target_expression = blocks.CharBlock(
        required=False,
        blank=True,
        label=_("Target expression"),
        help_text=_("Sent as 'target', e.g. bread.pk."),
    )
    confirm = blocks.CharBlock(
        max_length=255,
        required=False,
        blank=True,
        label=_("Confirmation text"),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        action_key = (value or {}).get("action", "")
        try:
            context["action_url"] = reverse(
                "wagtail_daisIE_dynamic:action", args=[action_key]
            )
        except NoReverseMatch:
            context["action_url"] = ""
        return context

    class Meta:
        icon = "plus"
        group = _("Data")
        collapsed = True
        template = "wagtail_daisIE/blocks/data/action_button.html"
        form_layout = blocks.BlockGroup(
            children=[
                "action",
                "label",
                "button_class",
                "target_expression",
                "confirm",
            ],
            settings=["design", "audience"],
        )


#: Blocks an admin can use to design a feed item or calendar event card —
#: the same set as a page body, plus action buttons.
ITEM_BLOCKS = [*PAGE_CONTENT_BLOCKS, ("action", ActionButtonBlock())]


class FeedBlock(ThemedBlock):
    """Render an admin-designed :class:`~wagtail_daisIE.dynamic.models.Feed`."""

    feed = SnippetChooserBlock("wagtail_daisIE.Feed", label=_("Feed"))

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        feed = (value or {}).get("feed")
        context.update(
            {
                "items_html": "",
                "has_more": False,
                "next_offset": 0,
                "total": 0,
                "page_size": 0,
                "filters": [],
                "feed_url": "",
            }
        )
        if feed is None:
            return context

        request = context.get("request")
        page = None
        if parent_context is not None and hasattr(parent_context, "get"):
            page = parent_context.get("page") or parent_context.get("self")
        try:
            offset = int((request.GET.get("offset") if request else 0) or 0)
        except (TypeError, ValueError):
            offset = 0

        context.update(render_feed(feed, request, offset=offset, page=page))
        try:
            context["feed_url"] = reverse(
                "wagtail_daisIE_dynamic:feed_items", args=[feed.pk]
            )
        except NoReverseMatch:
            context["feed_url"] = ""
        return context

    class Meta:
        icon = "list-ul"
        group = _("Data")
        collapsed = True
        template = "wagtail_daisIE/blocks/data/feed.html"
        form_layout = blocks.BlockGroup(
            children=["feed"],
            settings=["design", "audience"],
        )


class CalendarBlock(ThemedBlock):
    """A Cally date picker that shows each day's events as designed cards."""

    context_model = blocks.ChoiceBlock(
        choices=get_context_model_choices,
        label=_("Model"),
    )
    date_field = blocks.CharBlock(default="added_on", label=_("Date field"))
    event = blocks.StreamBlock(ITEM_BLOCKS, label=_("Event card"))
    initial_date = blocks.DateBlock(required=False, label=_("Initial date"))
    limit = blocks.IntegerBlock(
        min_value=1, max_value=500, default=200, label=_("Maximum events")
    )
    empty_message = blocks.CharBlock(
        max_length=255,
        required=False,
        blank=True,
        default="No events to show.",
        label=_("Empty message"),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
        context["cally_url"] = getattr(
            settings, "WAGTAIL_DAISIE_CALLY_URL", "https://unpkg.com/cally"
        )
        context["days"] = []
        initial = value.get("initial_date")

        key = value.get("context_model")
        config = get_context_model(key) if key else None
        date_field = (value.get("date_field") or "").strip()
        field = None
        if config is not None and config.model is not None and date_field:
            try:
                field = config.model._meta.get_field(date_field)
            except Exception:
                field = None
        if field is None:
            context["initial_iso"] = initial.isoformat() if initial else ""
            return context

        request, page = _request_and_page(parent_context)
        queryset = _base_queryset(config, request, page)
        if queryset is None:
            context["initial_iso"] = initial.isoformat() if initial else ""
            return context
        queryset = queryset.exclude(**{f"{date_field}__isnull": True}).order_by(
            date_field
        )
        objects = list(queryset[: int(value.get("limit") or 200)])
        base = _base_context(parent_context)
        stream = value.get("event")
        event_block = self.child_blocks["event"]
        grouped = OrderedDict()
        for obj in objects:
            raw = getattr(obj, date_field)
            day = raw.date() if hasattr(raw, "date") else raw
            if day is None:
                continue
            iso = day.isoformat()
            ctx = dict(base)
            ctx[key] = obj
            grouped.setdefault(iso, []).append(_render_stream(stream, ctx, event_block))

        context["days"] = [
            {"iso": iso, "events": events} for iso, events in grouped.items()
        ]
        if initial:
            context["initial_iso"] = initial.isoformat()
        elif context["days"]:
            context["initial_iso"] = context["days"][0]["iso"]
        else:
            context["initial_iso"] = date.today().isoformat()
        return context

    class Meta:
        icon = "date"
        group = _("Data")
        collapsed = True
        template = "wagtail_daisIE/blocks/data/calendar.html"
        form_layout = blocks.BlockGroup(
            children=[
                "context_model",
                "date_field",
                "event",
                "initial_date",
                "limit",
                "empty_message",
            ],
            settings=["design", "audience"],
        )


DATA_BLOCKS = [
    ("feed", FeedBlock()),
    ("calendar", CalendarBlock()),
    ("action", ActionButtonBlock()),
]
