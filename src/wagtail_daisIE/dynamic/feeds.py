"""Feed rendering: typed filters, slicing and item rendering.

A ``Feed`` snippet stores a context model, ordering, page size, the filters to
show and the admin-designed item blocks. The feed can be rendered server-side
(the initial page, and the no-JS fallback) or as a slice for the AJAX/infinite
endpoint.
"""

from __future__ import annotations

import logging

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db import models as django_models
from django.db.models import Q
from django.middleware.csrf import get_token
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from ..choices.utils import ChoiceList
from .context import context_model_keys
from .registry import get_context_model


logger = logging.getLogger(__name__)

FILTER_TYPES = (
    "choice",
    "boolean",
    "date",
    "date_range",
    "number_range",
    "search",
)


# --- Shared queryset/context helpers ---------------------------------------


def base_queryset(config, request=None, page=None):
    if config.model is None:
        return None
    queryset = config.get_queryset(request, page)
    if queryset is None:
        queryset = config.model._default_manager.all()
    if config.select_related:
        queryset = queryset.select_related(*config.select_related)
    if config.prefetch_related:
        queryset = queryset.prefetch_related(*config.prefetch_related)
    return queryset


def request_and_page(parent_context):
    request = None
    page = None
    if parent_context is not None and hasattr(parent_context, "get"):
        request = parent_context.get("request")
        page = parent_context.get("page") or parent_context.get("self")
    return request, page


def base_context(parent_context):
    from ..notifications.context import context_from_template_context

    base = {}
    if parent_context is None:
        return base
    base.update(context_from_template_context(parent_context))
    for key in context_model_keys():
        if key in parent_context:
            base[key] = parent_context[key]
    request = (
        parent_context.get("request", None) if hasattr(parent_context, "get") else None
    )
    if request is not None:
        base["request"] = request
    csrf_token = (
        parent_context.get("csrf_token", None)
        if hasattr(parent_context, "get")
        else None
    )
    if csrf_token is not None:
        base["csrf_token"] = csrf_token
    return base


def render_stream(stream, ctx, stream_block=None):
    """Render each child block of ``stream`` with the item context ``ctx``."""
    parts = []
    if not stream:
        return ""
    for child in stream:
        if hasattr(child, "block"):
            parts.append(str(child.block.render(child.value, ctx)))
        elif stream_block is not None and isinstance(child, dict) and "type" in child:
            block = stream_block.child_blocks.get(child["type"])
            if block is not None:
                parts.append(str(block.render(child.get("value"), ctx)))
        elif stream_block is not None and isinstance(child, (tuple, list)):
            if len(child) == 2:
                block = stream_block.child_blocks.get(child[0])
                if block is not None:
                    parts.append(str(block.render(child[1], ctx)))
    return "".join(parts)


# --- Filters ----------------------------------------------------------------


def resolve_choices(spec, request, page):
    source = spec.get("choices")
    if source is None:
        return []
    if callable(source):
        raw = _call(source, request, page)
    elif isinstance(source, (list, tuple)):
        raw = source
    else:
        try:
            raw = _call(import_string(source), request, page)
        except ImportError:
            logger.warning("Could not resolve filter choices %r", source)
            return []
    return _normalize_choices(raw)


def _call(func, request, page):
    try:
        return func(request, page)
    except TypeError:
        return func()


def _normalize_choices(raw):
    options = []
    for item in raw or []:
        if isinstance(item, dict):
            value = item.get("value")
            options.append(
                {"value": str(value), "label": str(item.get("label", value))}
            )
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            options.append({"value": str(item[0]), "label": str(item[1])})
        else:
            options.append({"value": str(item), "label": str(item)})
    return options


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except (TypeError, ValueError):
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            return None


def _parse_number(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (TypeError, InvalidOperation):
        return None


def apply_filters(queryset, config, params):
    """Apply the model's declared filters from GET/POST params."""
    if params is None:
        return queryset
    for key, spec in config.get_filters().items():
        try:
            queryset = _apply_one(queryset, config, key, spec, params)
        except Exception:  # pragma: no cover - defensive
            logger.debug("Ignoring invalid filter %r", key, exc_info=True)
    return queryset


def _date_transform(config, field):
    """Return the ORM path to filter a date, adding ``__date`` for datetimes."""
    base = field.split("__")[0]
    model_field = None
    if config is not None and config.model is not None:
        try:
            model_field = config.model._meta.get_field(base)
        except Exception:  # pragma: no cover - defensive
            model_field = None
    if isinstance(model_field, django_models.DateTimeField):
        return f"{field}__date"
    return field


def _apply_one(queryset, config, key, spec, params):
    filter_type = spec.get("type", "choice")
    field = spec.get("field")

    if filter_type == "choice":
        if spec.get("multi"):
            values = [v for v in params.getlist(f"filter_{key}") if v]
            if values:
                queryset = queryset.filter(**{f"{field}__in": values})
        else:
            value = params.get(f"filter_{key}")
            if value:
                queryset = queryset.filter(**{field: value})
    elif filter_type == "boolean":
        value = params.get(f"filter_{key}")
        if value in ("1", "true", "True", "yes", "on"):
            queryset = queryset.filter(**{field: True})
        elif value in ("0", "false", "False", "no", "off"):
            queryset = queryset.filter(**{field: False})
    elif filter_type == "date":
        value = _parse_date(params.get(f"filter_{key}"))
        if value is not None:
            queryset = queryset.filter(**{_date_transform(config, field): value})
    elif filter_type == "date_range":
        lookup = _date_transform(config, field)
        start = _parse_date(params.get(f"filter_{key}_from"))
        end = _parse_date(params.get(f"filter_{key}_to"))
        if start is not None:
            queryset = queryset.filter(**{f"{lookup}__gte": start})
        if end is not None:
            queryset = queryset.filter(**{f"{lookup}__lte": end})
    elif filter_type == "number_range":
        minimum = _parse_number(params.get(f"filter_{key}_min"))
        maximum = _parse_number(params.get(f"filter_{key}_max"))
        if minimum is not None:
            queryset = queryset.filter(**{f"{field}__gte": minimum})
        if maximum is not None:
            queryset = queryset.filter(**{f"{field}__lte": maximum})
    elif filter_type == "search":
        query = (params.get("feed_search") or "").strip()
        fields = spec.get("fields") or ([field] if field else [])
        if query and fields:
            condition = Q()
            for field_name in fields:
                condition |= Q(**{f"{field_name}__icontains": query})
            queryset = queryset.filter(condition)
    return queryset


def _selected_filters(feed):
    items = []
    for child in feed.filters or []:
        value = child.value if hasattr(child, "value") else child
        if isinstance(value, dict):
            items.append(value)
    return items


def build_filters(feed, config, params, request=None, page=None):
    """Return the UI definitions for the feed's selected filters."""
    from ..base_blocks.css import build_button_state_css, build_design_css

    filters = []
    for value in _selected_filters(feed):
        composite = (value.get("key") or "").strip()
        if not composite:
            continue
        model_key, _, filter_key = composite.partition(":")
        if model_key and model_key != feed.context_model:
            continue
        spec = config.get_filters().get(filter_key)
        if not spec:
            continue
        filter_type = spec.get("type", "choice")
        appearance = value.get("button_appearance") or {}
        active_state = appearance.get("active") if hasattr(appearance, "get") else None
        entry = {
            "key": filter_key,
            "type": filter_type,
            "label": value.get("label")
            or spec.get("label")
            or filter_key.replace("_", " ").title(),
            "multi": bool(spec.get("multi")),
            "collapsed": bool(value.get("collapsed")),
            "button_css": build_design_css(
                {"button_appearance": value.get("button_appearance")}
            )
            or "btn",
            "selected_css": build_button_state_css(active_state),
            "input_css": build_design_css(value.get("input_design")),
            "label_css": build_design_css(value.get("label_design")),
            "value": params.get(f"filter_{filter_key}", "") if params else "",
            "values": params.getlist(f"filter_{filter_key}") if params else [],
            "from": params.get(f"filter_{filter_key}_from", "") if params else "",
            "to": params.get(f"filter_{filter_key}_to", "") if params else "",
            "min": params.get(f"filter_{filter_key}_min", "") if params else "",
            "max": params.get(f"filter_{filter_key}_max", "") if params else "",
        }
        if filter_type == "boolean":
            entry["options"] = [
                {"value": "1", "label": "Yes"},
                {"value": "0", "label": "No"},
            ]
        elif filter_type == "choice":
            entry["options"] = resolve_choices(spec, request, page)
        filters.append(entry)
    return filters


# --- Layout -----------------------------------------------------------------

#: Literal strings so Tailwind's scanner picks up every class.
GRID_COLUMNS = {
    1: "grid-cols-1",
    2: "grid-cols-1 sm:grid-cols-2",
    3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
    5: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-5",
    6: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-6",
}

#: The two layouts a toggle switches between, keyed by the stored choice.
TOGGLE_PAIRS = {
    "grid_list": ("grid", "list"),
    "grid_row": ("grid", "row"),
    "row_list": ("row", "list"),
}

# --- Layout choices ---------------------------------------------------------
#
# These are the single source of truth: the ``Feed`` model fields, the
# ``FeedLayoutOverrideBlock`` block and :func:`resolve_layout` all read them.
# They live here rather than on the model because ``blocks_data`` needs them
# and ``models`` imports ``blocks_data``.

LAYOUT_CHOICES = ChoiceList(
    [
        ("grid", _("Grid")),
        ("row", _("Row")),
        ("list", _("List")),
    ],
    "LAYOUT_CHOICES",
)
ROW_MODE_CHOICES = ChoiceList(
    [
        ("wrap", _("Wrap onto new lines")),
        ("scroll", _("Scroll horizontally")),
    ],
    "ROW_MODE_CHOICES",
)
GAP_CHOICES = ChoiceList(
    [
        ("gap-1", "1"),
        ("gap-2", "2"),
        ("gap-3", "3"),
        ("gap-4", "4"),
        ("gap-6", "6"),
        ("gap-8", "8"),
    ],
    "GAP_CHOICES",
)
TOGGLE_LABELS = {
    "grid_list": _("Grid / List"),
    "grid_row": _("Grid / Row"),
    "row_list": _("Row / List"),
}
TOGGLE_CHOICES = ChoiceList(
    [(key, TOGGLE_LABELS[key]) for key in TOGGLE_PAIRS], "TOGGLE_CHOICES"
)

#: Layout key -> translated label, for the visitor toggle.
LAYOUT_LABELS = dict(LAYOUT_CHOICES)


# Plain accessors so model fields (which Django materialises from iterables)
# serialize as short function references instead of the full choice lists.
def layout_choices():
    return LAYOUT_CHOICES


def gap_choices():
    return GAP_CHOICES


def row_mode_choices():
    return ROW_MODE_CHOICES


def toggle_choices():
    return TOGGLE_CHOICES


def layout_class_map(feed, override=None):
    """Return ``{layout: container_css}`` for a feed (and block override)."""
    override = override or {}
    columns = override.get("columns") or getattr(feed, "layout_columns", 3) or 3
    if columns not in GRID_COLUMNS:
        columns = 3
    gap = override.get("gap") or getattr(feed, "layout_gap", "gap-4") or "gap-4"
    row_mode = override.get("row_mode") or getattr(feed, "row_mode", "wrap") or "wrap"
    if row_mode == "scroll":
        row = (
            f"flex flex-row flex-nowrap {gap} overflow-x-auto snap-x "
            "daisie-feed--row daisie-feed--row-scroll"
        )
    else:
        row = f"flex flex-row flex-wrap {gap} daisie-feed--row"
    return {
        "grid": f"grid {gap} {GRID_COLUMNS[columns]} daisie-feed--grid",
        "row": row,
        "list": "divide-y divide-base-300 daisie-feed--list",
    }


def resolve_layout(feed, override=None, request=None):
    """Resolve the active layout, its classes and the visitor toggle options."""
    override = override or {}
    classes = layout_class_map(feed, override)

    layout = override.get("layout") or getattr(feed, "layout", "grid") or "grid"
    if layout not in classes:
        layout = "grid"

    show = override.get("show_toggle")
    if show == "yes":
        allow_toggle = True
    elif show == "no":
        allow_toggle = False
    else:
        allow_toggle = bool(getattr(feed, "allow_layout_toggle", False))

    toggle_layouts = (
        override.get("toggle_layouts")
        or getattr(feed, "toggle_layouts", "grid_list")
        or "grid_list"
    )
    option_keys = (
        TOGGLE_PAIRS.get(toggle_layouts, ("grid", "list")) if allow_toggle else []
    )
    options = [{"value": key, "label": LAYOUT_LABELS[key]} for key in option_keys]

    requested = (getattr(request, "GET", None) or {}).get("layout") if request else None
    if requested in classes and requested in (option_keys or classes):
        layout = requested

    return {
        "layout": layout,
        "layout_classes": classes,
        "layout_container_css": classes[layout],
        "toggle_options": options,
        "allow_layout_toggle": allow_toggle,
        "item_css": "daisie-feed__item",
    }


# --- Rendering --------------------------------------------------------------


def render_feed(feed, request, offset=0, limit=None, page=None, override=None):
    """Render a slice of ``feed`` and return the template context data."""
    config = get_context_model(feed.context_model)
    result = {
        "items_html": "",
        "has_more": False,
        "next_offset": offset,
        "total": 0,
        "page_size": feed.page_size,
        "filters": [],
        "submit_css": "btn",
    }
    result.update(resolve_layout(feed, override, request))
    get_submit_css = getattr(feed, "get_submit_css", None)
    if callable(get_submit_css):
        result["submit_css"] = get_submit_css()
    if config is None or config.model is None:
        return result

    params = getattr(request, "GET", None)
    queryset = base_queryset(config, request, page)
    if queryset is None:
        return result
    queryset = apply_filters(queryset, config, params)

    order_by = (feed.order_by or "").strip()
    if order_by:
        try:
            config.model._meta.get_field(order_by.lstrip("-"))
        except Exception:
            order_by = ""
        else:
            queryset = queryset.order_by(order_by)

    result["total"] = queryset.count()
    try:
        page_size = max(1, int(feed.page_size or 9))
    except (TypeError, ValueError):
        page_size = 9
    result["page_size"] = page_size
    if limit is not None:
        try:
            end = max(0, int(limit))
        except (TypeError, ValueError):
            end = page_size
        objects = list(queryset[:end])
        result["next_offset"] = end
    else:
        try:
            offset = max(0, int(offset))
        except (TypeError, ValueError):
            offset = 0
        objects = list(queryset[offset : offset + page_size])
        result["next_offset"] = offset + page_size
    result["next_limit"] = result["next_offset"] + page_size
    result["has_more"] = result["next_offset"] < result["total"]
    result["filters"] = build_filters(feed, config, params, request, page)

    if not objects:
        return result

    base = _items_context(request, page)
    item_block = feed._meta.get_field("item").stream_block
    items = []
    for obj in objects:
        ctx = dict(base)
        ctx[config.key] = obj
        items.append(render_stream(feed.item, ctx, item_block))
    item_css = result.get("item_css", "daisie-feed__item")
    result["items_html"] = "".join(
        f'<div class="{item_css}" data-daisie-feed-item>{html}</div>' for html in items
    )
    return result


def _items_context(request, page):
    from ..notifications.context import build_context
    from .resolvers import resolve_context_models

    base = build_context(request=request)
    base.update(resolve_context_models(request, page))
    if request is not None:
        base["request"] = request
        base["csrf_token"] = get_token(request)
    return base
