"""django-filter integration for feed filters."""

from __future__ import annotations

import logging

from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db import models as django_models
from django.db.models import Q
from django.utils.module_loading import import_string
from django_filters import FilterSet, filters
from django_filters.widgets import BooleanWidget, RangeWidget


logger = logging.getLogger(__name__)


class _DateRangeWidget(RangeWidget):
    """Range widget whose parameter names match the feed's existing names."""

    suffixes = ["from", "to"]


class _PermissiveMultipleChoiceField(forms.MultipleChoiceField):
    """Accept arbitrary values, because choices are resolved at render time."""

    def valid_value(self, value):
        return True


class FeedMultipleChoiceFilter(filters.MultipleChoiceFilter):
    field_class = _PermissiveMultipleChoiceField


class FeedQueryFilter(filters.Filter):
    """A filter that delegates to a configured ``query`` callable."""

    def __init__(self, query, key, **kwargs):
        self.query = query
        self.key = key
        super().__init__(**kwargs)

    def filter(self, qs, value):
        return self.query(qs, self.parent.data, self.key)


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


def _resolve_query(query):
    if isinstance(query, str):
        try:
            return import_string(query)
        except ImportError:
            logger.warning("Could not resolve feed query %r", query)
            return None
    return query if callable(query) else None


def build_filterset(config):
    """Build a cached, dynamic FilterSet for a context model."""

    model = config.model
    attrs = {}
    search_specs = []

    for key, spec in config.get_filters().items():
        filter_type = spec.get("type", "choice")
        if filter_type == "sort":
            continue

        name = f"filter_{key}"
        field = spec.get("field")

        query = _resolve_query(spec.get("query"))
        if query is not None:
            attrs[name] = FeedQueryFilter(
                query, key, field_name=key, label=spec.get("label")
            )
            continue

        if filter_type == "search":
            search_specs.append((key, spec))
            continue

        if not field:
            continue

        if filter_type == "choice":
            if spec.get("multi"):
                attrs[name] = FeedMultipleChoiceFilter(
                    field_name=field,
                    lookup_expr="in",
                    distinct=False,
                )
            else:
                attrs[name] = filters.CharFilter(field_name=field)
        elif filter_type == "boolean":
            attrs[name] = filters.BooleanFilter(
                field_name=field,
                widget=BooleanWidget(),
            )
        elif filter_type == "date":
            attrs[name] = filters.DateFilter(field_name=_date_transform(config, field))
        elif filter_type == "date_range":
            attrs[name] = filters.DateFromToRangeFilter(
                field_name=_date_transform(config, field),
                widget=_DateRangeWidget(),
            )
        elif filter_type == "number_range":
            attrs[name] = filters.RangeFilter(field_name=field)
        elif filter_type == "search":
            search_specs.append((key, spec))

    if search_specs:

        def filter_search(qs, name, value):
            for _key, spec in search_specs:
                fields = spec.get("fields") or (
                    [spec.get("field")] if spec.get("field") else []
                )
                if not fields:
                    continue
                condition = Q()
                for field_name in fields:
                    condition |= Q(**{f"{field_name}__icontains": value})
                qs = qs.filter(condition)
            return qs

        attrs["feed_search"] = filters.CharFilter(method=filter_search)

    attrs["Meta"] = type("Meta", (), {"model": model, "fields": []})
    return type(f"{model.__name__}FeedFilterSet", (FilterSet,), attrs)


# Re-export for existing tests and callers.
_date_transform = _date_transform
