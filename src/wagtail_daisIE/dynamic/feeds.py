"""Feed rendering: typed filters, slicing and item rendering.

A ``Feed`` snippet stores a context model, ordering, page size, the filters to
show and the admin-designed item blocks. The feed can be rendered server-side
(the initial page, and the no-JS fallback) or as a slice for the AJAX/infinite
endpoint.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.core import signing
from django.core.exceptions import FieldDoesNotExist, FieldError
from django.core.paginator import (
    EmptyPage,
    Page,
    PageNotAnInteger,
    Paginator,
)
from django.db import models as django_models
from django.http import QueryDict
from django.middleware.csrf import get_token
from django.urls import NoReverseMatch, reverse
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from ..choices.utils import ChoiceList
from .context import context_model_keys
from .querysets import base_queryset, call_with_request_page
from .registry import get_context_model


logger = logging.getLogger(__name__)

# --- Countless pagination ---------------------------------------------------


class CountlessPage(Page):
    """A ``Page`` that knows its next page without calling ``count``."""

    def __init__(self, object_list, number, paginator, has_next=False):
        super().__init__(object_list, number, paginator)
        self._has_next = bool(has_next)

    def has_next(self):
        return self._has_next

    def has_previous(self):
        return self.number > 1

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def next_page_number(self):
        if not self.has_next():
            raise EmptyPage("There is no next page.")
        return self.number + 1

    def previous_page_number(self):
        if not self.has_previous():
            raise EmptyPage("There is no previous page.")
        return self.number - 1

    def start_index(self):
        if not self.object_list:
            return 0
        return (self.number - 1) * self.paginator.per_page + 1

    def end_index(self):
        if not self.object_list:
            return 0
        return (self.number - 1) * self.paginator.per_page + len(self.object_list)


class CountlessPaginator(Paginator):
    """Fetch ``per_page + 1`` rows and derive ``has_next`` from the extra row."""

    def validate_number(self, number):
        try:
            number = int(number)
        except (TypeError, ValueError) as exc:
            raise PageNotAnInteger("That page number is not an integer.") from exc
        if number < 1:
            raise EmptyPage("That page number is less than 1.")
        return number

    def page(self, number):
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page + 1
        rows = list(self.object_list[bottom:top])
        has_next = len(rows) > self.per_page
        if has_next:
            rows = rows[: self.per_page]
        return CountlessPage(rows, number, self, has_next=has_next)

    def get_page(self, number):
        try:
            return self.page(number)
        except (PageNotAnInteger, EmptyPage):
            return self.page(1)


def paginate_queryset(queryset, per_page, number):
    """Return ``(page_obj, total)`` using the countless paginator by default.

    ``total`` is ``None`` under the countless paginator. If the subclass is
    rejected, fall back to the stock ``Paginator`` and return its count (one
    count query per request).
    """
    try:
        paginator = CountlessPaginator(queryset, per_page)
    except TypeError as exc:
        logger.warning(
            "CountlessPaginator rejected; falling back to Paginator: %s", exc
        )
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(number)
        return page_obj, paginator.count
    try:
        page_obj = paginator.get_page(number)
    except TypeError as exc:
        logger.warning(
            "CountlessPaginator rejected; falling back to Paginator: %s", exc
        )
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(number)
        return page_obj, paginator.count
    return page_obj, None


FILTER_TYPES = (
    "choice",
    "boolean",
    "date",
    "date_range",
    "number_range",
    "search",
    "sort",
)

DEFAULT_FEED_MAX_LIMIT = 1000
DEFAULT_FEED_MAX_OFFSET = 1_000_000
DEFAULT_CHOICE_LIMIT = 100
DEFAULT_AUTOCOMPLETE_CHOICE_LIMIT = 20
LAYOUT_OVERRIDE_NAMESPACE = "wagtail_daisIE.feed_layout"


def _positive_setting(name, default):
    raw = getattr(settings, name, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        logger.warning("Invalid %s setting %r; using %r", name, raw, default)
        return default
    if value < 1:
        logger.warning("Invalid %s setting %r; using %r", name, raw, default)
        return default
    return value


def feed_max_limit():
    return _positive_setting("WAGTAIL_DAISIE_FEED_MAX_LIMIT", DEFAULT_FEED_MAX_LIMIT)


def feed_max_offset():
    return _positive_setting("WAGTAIL_DAISIE_FEED_MAX_OFFSET", DEFAULT_FEED_MAX_OFFSET)


def bounded_int(value, *, default, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        return default
    return max(minimum, min(parsed, maximum))


def normalise_layout_override(override):
    if not override:
        return {}
    try:
        data = dict(override)
    except (TypeError, ValueError):
        return {}
    return {key: value for key, value in data.items() if value not in (None, "")}


def encode_layout_override(override):
    data = normalise_layout_override(override)
    if not data:
        return ""
    return signing.dumps(data, salt=LAYOUT_OVERRIDE_NAMESPACE, compress=True)


def decode_layout_override(token):
    if not token:
        return {}
    try:
        data = signing.loads(token, salt=LAYOUT_OVERRIDE_NAMESPACE)
    except (signing.BadSignature, TypeError, ValueError):
        logger.warning("Ignoring invalid feed layout token")
        return {}
    return normalise_layout_override(data)


def _page_url(
    request, page_number, *, source_page=None, layout_token="", legacy_limit=None
):
    if request is not None:
        params = request.GET.copy()
    else:
        params = QueryDict(mutable=True)

    for key in ("page", "offset", "block", "fragment", "layout_token"):
        params.pop(key, None)

    params["page"] = str(page_number)
    if legacy_limit is not None:
        params["limit"] = str(legacy_limit)
    else:
        params.pop("limit", None)
    if layout_token:
        params["layout_token"] = layout_token
    if source_page is not None and getattr(source_page, "pk", None):
        params["source_page"] = str(source_page.pk)
    else:
        params.pop("source_page", None)

    return f"?{params.urlencode()}"


# --- Shared queryset/context helpers ---------------------------------------


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


def render_stream(stream, ctx, stream_block=None, scope=None):
    """Render each child block of ``stream`` with the item context ``ctx``."""
    parts = []
    if not stream:
        return ""
    if scope:
        ctx = {**ctx, "daisie_visibility_scope": scope}
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


def _raw_choices(spec, request, page):
    source = spec.get("choices")
    if source is None:
        return []
    try:
        if callable(source):
            raw = call_with_request_page(source, request, page)
        elif isinstance(source, (list, tuple)):
            raw = source
        else:
            try:
                target = import_string(source)
            except ImportError:
                logger.warning("Could not resolve filter choices %r", source)
                return []
            if not callable(target):
                logger.warning("Filter choices source %r is not callable.", source)
                return []
            raw = call_with_request_page(target, request, page)
        return _normalize_choices(raw)
    except (TypeError, ValueError, ImportError) as exc:
        logger.warning("Failed to resolve filter choices %r: %s", source, exc)
        return []


def _choice_limit(spec):
    if spec.get("autocomplete"):
        default = DEFAULT_AUTOCOMPLETE_CHOICE_LIMIT
    else:
        default = DEFAULT_CHOICE_LIMIT
    raw = spec.get("choice_limit", default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default
    if value < 1:
        value = default
    return min(value, feed_max_limit())


def _selected_values(params, key):
    if params is None:
        return []
    try:
        values = params.getlist(f"filter_{key}")
    except AttributeError:
        value = params.get(f"filter_{key}")
        values = [value] if value not in (None, "") else []
    return [str(item) for item in values if item not in (None, "")]


def _limit_choices(options, selected, limit):
    selected = [str(value) for value in selected]
    selected_set = set(selected)
    base = options[:limit]
    present = {option["value"] for option in base}
    extras = [
        option
        for option in options
        if option["value"] in selected_set and option["value"] not in present
    ]
    known = {option["value"] for option in options}
    missing = [
        {"value": value, "label": value} for value in selected if value not in known
    ]
    return base + extras + missing


def resolve_choice_options(spec, request, page, *, selected=(), query="", limit=None):
    """Resolve a filter's choices and bound them.

    Returns ``(options, truncated)``. ``truncated`` is true when the unbounded
    choice list (after applying ``query``) is larger than the limit.
    """
    options = _raw_choices(spec, request, page)
    if query:
        needle = query.casefold()
        options = [
            option
            for option in options
            if needle in option["value"].casefold()
            or needle in option["label"].casefold()
        ]
    total = len(options)
    if limit is None:
        limit = _choice_limit(spec)
    if not query:
        options = _limit_choices(options, selected, limit)
    else:
        options = options[:limit]
    return options, total > limit


def resolve_choices(spec, request, page, *, selected=(), query="", limit=None):
    """Compatibility wrapper returning only the option list."""
    options, _ = resolve_choice_options(
        spec, request, page, selected=selected, query=query, limit=limit
    )
    return options


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


def bind_filters(queryset, config, params, request=None):
    """Bind ``params`` to a django-filter FilterSet for ``config``."""
    filterset_class = getattr(config, "filterset_class", None)
    if filterset_class is None:
        return None
    try:
        return filterset_class(data=params, queryset=queryset, request=request)
    except (FieldError, TypeError, ValueError) as exc:
        logger.warning("Ignoring invalid feed filters: %s", exc)
        return None


def apply_filters(queryset, config, params):
    """Apply the model's declared filters from GET/POST params."""
    if params is None:
        return queryset
    filterset = bind_filters(queryset, config, params)
    if filterset is None:
        return queryset
    try:
        return filterset.qs
    except (FieldError, TypeError, ValueError) as exc:
        logger.warning("Ignoring invalid feed filters: %s", exc)
        return queryset


def _date_transform(config, field):
    """Return the ORM path to filter a date, adding ``__date`` for datetimes."""
    base = field.split("__")[0]
    model_field = None
    if config is not None and config.model is not None:
        try:
            model_field = config.model._meta.get_field(base)
        except FieldDoesNotExist:
            model_field = None
    if isinstance(model_field, django_models.DateTimeField):
        return f"{field}__date"
    return field


def _selected_filters(feed):
    items = []
    for child in feed.filters or []:
        value = child.value if hasattr(child, "value") else child
        if isinstance(value, dict):
            items.append(value)
    return items


def _first_stream_value(stream_field):
    if not stream_field:
        return {}
    child = stream_field[0]
    value = child.value if hasattr(child, "value") else child
    return value if isinstance(value, dict) else {}


def build_filter_menu(feed):
    """Return the optional feed filter-menu configuration."""
    from ..base_blocks.css import build_design_css

    value = _first_stream_value(feed.filter_menu)
    if not value or not value.get("enabled"):
        return {"enabled": False}
    return {
        "enabled": True,
        "label": value.get("label") or "Filters",
        "icon": value.get("icon"),
        "style": value.get("style") or "dropdown",
        "default_open": bool(value.get("default_open")),
        "include_layout_toggle": bool(value.get("include_layout_toggle")),
        "trigger_css": build_design_css(
            {"button_appearance": value.get("trigger_appearance")}
        )
        or "btn",
        "panel_css": build_design_css(value.get("panel_design")),
        "container_css": build_design_css(value.get("container_design")),
    }


def _reset_url(request, params, filter_key):
    if request is None or not getattr(request, "path", ""):
        return ""

    query = params.copy() if params is not None else QueryDict(mutable=True)
    for suffix in ("", "_from", "_to", "_min", "_max"):
        query.pop(f"filter_{filter_key}{suffix}", None)

    encoded = query.urlencode()
    return f"{request.path}?{encoded}" if encoded else request.path


def _bound_field(filterset, name):
    if filterset is None or not hasattr(filterset, "form"):
        return None
    form = filterset.form
    if name not in form.fields:
        return None
    return form[name]


def _bound_filter_value(filterset, name, params, fallback_name):
    field = _bound_field(filterset, name)
    if field is not None:
        value = field.value()
        if isinstance(value, bool):
            return "1" if value else "0"
        if value in (None, ""):
            return params.get(fallback_name, "") if params else ""
        return (
            value
            if not isinstance(value, (list, tuple))
            else (value[0] if value else "")
        )
    if params is None:
        return ""
    return params.get(fallback_name, "")


def _bound_filter_values(filterset, name, params, fallback_name):
    field = _bound_field(filterset, name)
    if field is not None:
        value = field.value()
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value if item not in (None, "")]
        if value in (None, ""):
            return params.getlist(fallback_name) if params else []
        return [str(value)]
    if params is None:
        return []
    return params.getlist(fallback_name)


def _bound_filter_range(filterset, name, params, suffix):
    field = _bound_field(filterset, name)
    if field is not None:
        value = field.value()
        if isinstance(value, (list, tuple)):
            index = 0 if suffix in ("_from", "_min") else 1
            if len(value) > index:
                item = value[index]
                return "" if item in (None, "") else str(item)
    if params is None:
        return ""
    return params.get(f"{name}{suffix}", "")


def build_filters(
    feed,
    config,
    params,
    request=None,
    page=None,
    selected_filters=None,
    resolved_choices=None,
    filter_menu=None,
    filterset=None,
):
    """Return the UI definitions for the feed's selected filters."""
    from ..base_blocks.css import build_button_state_css, build_design_css
    from ..base_blocks.utils import build_class

    if filter_menu is None:
        filter_menu = build_filter_menu(feed)
    menu_enabled = filter_menu.get("enabled")
    if selected_filters is None:
        selected_filters = _selected_filters(feed)
    filters = []
    for value in selected_filters:
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
        menu_item_css = build_design_css(value.get("menu_item_design"))
        entry = {
            "key": filter_key,
            "type": filter_type,
            "label": value.get("label")
            or spec.get("label")
            or filter_key.replace("_", " ").title(),
            "multi": bool(spec.get("multi")),
            "autocomplete": bool(spec.get("autocomplete")),
            "collapsed": bool(value.get("collapsed")),
            "container_css": build_class(
                build_design_css(value.get("container_design")),
                menu_item_css if menu_enabled else "",
            ),
            "menu_item_css": menu_item_css,
            "button_css": build_design_css(
                {"button_appearance": value.get("button_appearance")}
            )
            or "btn",
            "selected_css": build_button_state_css(active_state),
            "input_css": build_design_css(value.get("input_design")),
            "label_css": build_design_css(value.get("label_design")),
            "value": _bound_filter_value(
                filterset, f"filter_{filter_key}", params, f"filter_{filter_key}"
            ),
            "values": _bound_filter_values(
                filterset, f"filter_{filter_key}", params, f"filter_{filter_key}"
            ),
            "from": _bound_filter_range(
                filterset, f"filter_{filter_key}", params, "_from"
            ),
            "to": _bound_filter_range(filterset, f"filter_{filter_key}", params, "_to"),
            "min": _bound_filter_range(
                filterset, f"filter_{filter_key}", params, "_min"
            ),
            "max": _bound_filter_range(
                filterset, f"filter_{filter_key}", params, "_max"
            ),
            "reset_url": _reset_url(request, params, filter_key),
            "remote_url": "",
        }
        if filter_type == "boolean":
            entry["options"] = [
                {"value": "1", "label": "Yes"},
                {"value": "0", "label": "No"},
            ]
        elif filter_type in ("choice", "sort", "autocomplete"):
            if resolved_choices is not None and filter_key in resolved_choices:
                resolved = resolved_choices[filter_key]
                entry["options"] = resolved["options"]
                truncated = resolved["truncated"]
            else:
                selected = _selected_values(params, filter_key)
                entry["options"], truncated = resolve_choice_options(
                    spec, request, page, selected=selected
                )
            if entry["autocomplete"] and truncated:
                entry["remote_url"] = _filter_choices_url(feed, filter_key, page)
        filters.append(entry)
    return filters


def resolve_order(
    feed,
    config,
    params,
    request=None,
    page=None,
    selected_filters=None,
    resolved_choices=None,
):
    """Return the order_by for a feed, honouring a visitor ``sort`` filter."""
    order_by = (feed.order_by or "").strip()
    if params is None:
        return order_by
    if selected_filters is None:
        selected_filters = _selected_filters(feed)
    selected = {
        (value.get("key") or "").partition(":")[2] for value in selected_filters
    }
    for key, spec in config.get_filters().items():
        if spec.get("type") != "sort" or key not in selected:
            continue
        value = params.get(f"filter_{key}")
        if not value:
            continue
        if resolved_choices is not None and key in resolved_choices:
            allowed = {str(item["value"]) for item in resolved_choices[key]["options"]}
        else:
            selected_values = _selected_values(params, key)
            allowed = {
                str(item["value"])
                for item in resolve_choices(
                    spec, request, page, selected=selected_values
                )
            }
        if str(value) in allowed:
            return str(value)
    return order_by


def _filter_choices_url(feed, filter_key, page):
    try:
        url = reverse(
            "wagtail_daisIE_dynamic:feed_filter_choices",
            args=[feed.pk, filter_key],
        )
    except NoReverseMatch:
        return ""
    if page is not None and getattr(page, "pk", None):
        params = QueryDict(mutable=True)
        params["source_page"] = str(page.pk)
        url = f"{url}?{params.urlencode()}"
    return url


def _resolve_filter_choices(feed, config, params, request, page, selected_filters=None):
    """Resolve each selected filter's choices once per request."""
    if selected_filters is None:
        selected_filters = _selected_filters(feed)
    resolved = {}
    for value in selected_filters:
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
        if filter_type not in ("choice", "sort", "autocomplete"):
            continue
        selected = _selected_values(params, filter_key)
        options, truncated = resolve_choice_options(
            spec, request, page, selected=selected
        )
        resolved[filter_key] = {"options": options, "truncated": truncated}
    return resolved


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
    if allow_toggle and requested in option_keys:
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


def render_feed(
    feed,
    request,
    page_number=None,
    source_page=None,
    override=None,
    layout_token="",
):
    """Render a page of ``feed`` and return the template context data."""
    from ..base_blocks.css import build_button_state_css, build_design_css

    config = get_context_model(feed.context_model)
    layout_appearance = _first_stream_value(feed.layout_toggle_appearance)
    filter_menu = build_filter_menu(feed)
    result = {
        "items_html": "",
        "has_more": False,
        "has_previous": False,
        "previous_url": "",
        "next_url": "",
        "next_page_number": 1,
        "page_number": 1,
        "page_size": feed.page_size,
        "total": None,
        "filters": [],
        "submit_css": "btn",
        "filter_menu": filter_menu,
        "filter_panel_css": build_design_css(
            _first_stream_value(feed.filter_panel_design)
        ),
        "filter_layout_css": build_design_css(_first_stream_value(feed.filter_layout)),
        "layout_toggle_css": build_design_css({"button_appearance": layout_appearance})
        or "btn btn-sm",
        "layout_toggle_selected_css": build_button_state_css(
            (layout_appearance or {}).get("active")
        ),
        "layout_token": layout_token,
        "source_page_pk": (
            str(source_page.pk)
            if source_page is not None and getattr(source_page, "pk", None)
            else ""
        ),
        "infinite": bool(getattr(feed, "infinite", False)),
    }
    result.update(resolve_layout(feed, override, request))
    get_submit_css = getattr(feed, "get_submit_css", None)
    if callable(get_submit_css):
        result["submit_css"] = get_submit_css()
    if config is None or config.model is None:
        return result

    params = getattr(request, "GET", None)
    queryset = base_queryset(config, request, source_page)
    if queryset is None:
        return result
    filterset = bind_filters(queryset, config, params, request=request)
    if filterset is not None:
        queryset = filterset.qs

    selected_filters = _selected_filters(feed)
    resolved_choices = _resolve_filter_choices(
        feed, config, params, request, source_page, selected_filters
    )

    order_by = resolve_order(
        feed,
        config,
        params,
        request,
        source_page,
        selected_filters=selected_filters,
        resolved_choices=resolved_choices,
    )
    if order_by:
        field_name = order_by.lstrip("-")
        if field_name == "pk":
            field_name = config.model._meta.pk.name
        try:
            config.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            order_by = ""
        else:
            queryset = queryset.order_by(order_by)

    max_limit = feed_max_limit()
    try:
        page_size = int(feed.page_size or 9)
    except (TypeError, ValueError):
        page_size = 9
    page_size = min(max(1, page_size), max_limit)
    result["page_size"] = page_size

    max_offset = feed_max_offset()
    max_pages = max(1, max_offset // page_size + 1)

    legacy_limit = None
    raw_limit = params.get("limit") if params is not None else None
    if raw_limit not in (None, ""):
        try:
            parsed_limit = int(raw_limit)
        except (TypeError, ValueError):
            parsed_limit = None
        if parsed_limit is not None:
            legacy_limit = min(max(1, parsed_limit), max_limit)
            per_page = legacy_limit
        else:
            per_page = page_size
    else:
        per_page = page_size

    if page_number is None:
        page_number = params.get("page") if params is not None else None
    try:
        requested_page = int(page_number)
    except (TypeError, ValueError):
        requested_page = None

    raw_offset = params.get("offset") if params is not None else None
    if requested_page is None and raw_offset not in (None, ""):
        try:
            parsed_offset = int(raw_offset)
        except (TypeError, ValueError):
            parsed_offset = 0
        parsed_offset = max(0, min(parsed_offset, max_offset))
        requested_page = parsed_offset // per_page + 1

    if requested_page is None:
        requested_page = 1
    requested_page = max(1, min(requested_page, max_pages))

    page_obj, total = paginate_queryset(queryset, per_page, requested_page)
    result["total"] = total
    result["page_number"] = page_obj.number
    result["has_more"] = bool(page_obj.has_next())
    result["has_previous"] = bool(page_obj.has_previous())
    result["next_page_number"] = (
        page_obj.next_page_number() if result["has_more"] else result["page_number"]
    )

    result["next_url"] = _page_url(
        request,
        result["next_page_number"],
        source_page=source_page,
        layout_token=layout_token,
        legacy_limit=legacy_limit,
    )
    result["previous_url"] = (
        _page_url(
            request,
            max(1, result["page_number"] - 1),
            source_page=source_page,
            layout_token=layout_token,
            legacy_limit=legacy_limit,
        )
        if result["has_previous"]
        else ""
    )
    result["filters"] = build_filters(
        feed,
        config,
        params,
        request,
        source_page,
        selected_filters=selected_filters,
        resolved_choices=resolved_choices,
        filter_menu=filter_menu,
        filterset=filterset,
    )

    objects = list(page_obj.object_list)
    if not objects:
        return result

    base = _items_context(request, source_page)
    stream = feed.item
    stream_block = feed._meta.get_field("item").stream_block
    items = []
    for obj in objects:
        ctx = dict(base)
        ctx[config.key] = obj
        items.append(render_stream(stream, ctx, stream_block, scope="feed-item"))
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
