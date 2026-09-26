"""Registry of model detail-page bridges.

Projects declare which context models get a dedicated Wagtail page::

    WAGTAIL_DAISIE_DETAIL_PAGES = {
        "bread": {
            "label": _("Bread"),
            "model": "blog.Bread",
            "page_type": "blog.BreadDetailPage",
            "parent": "blog.BreadDetailTemplate",
            "template_page": "blog.BreadDetailTemplate",
            "lookup_field": "slug",
            "lookup_in": "path",
            "publish_field": "is_available",
            "title_source": "name",
            "slug_source": "name",
        },
    }

Nothing here touches the database at import time.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass, field

from django.conf import settings

from ..dynamic.registry import resolve_model


logger = logging.getLogger(__name__)

SETTING_NAME = "WAGTAIL_DAISIE_DETAIL_PAGES"

_detail_pages_cache: dict[str, DetailPageConfig] | None = None


@dataclass
class DetailPageConfig:
    """A single entry from ``WAGTAIL_DAISIE_DETAIL_PAGES``."""

    key: str
    label: object
    model_path: str = ""
    page_type_path: str = ""
    parent_path: str = ""
    template_page_path: str = ""
    lookup_field: str = "pk"
    lookup_in: str = "path"
    publish_field: str = ""
    title_source: str = "title"
    slug_source: str = "slug"
    on_delete: str = "page"
    _resolved_model: object = field(default=None, repr=False)
    _resolved_page_type: object = field(default=None, repr=False)
    _resolved_parent: object = field(default=None, repr=False)
    _resolved_template_page: object = field(default=None, repr=False)

    @property
    def model(self):
        if self._resolved_model is None:
            self._resolved_model = resolve_model(self.model_path)
        return self._resolved_model

    @property
    def page_type(self):
        if self._resolved_page_type is None:
            self._resolved_page_type = resolve_model(self.page_type_path)
        return self._resolved_page_type

    @property
    def parent_model(self):
        if self._resolved_parent is None:
            self._resolved_parent = resolve_model(self.parent_path)
        return self._resolved_parent

    @property
    def template_page_model(self):
        if self._resolved_template_page is None:
            self._resolved_template_page = resolve_model(
                self.template_page_path or self.parent_path
            )
        return self._resolved_template_page

    def __str__(self):
        return str(self.label or self.key)


def _build_detail_page(key, raw):
    raw = dict(raw or {})
    return DetailPageConfig(
        key=key,
        label=raw.get("label") or key.replace("_", " ").title(),
        model_path=raw.get("model", ""),
        page_type_path=raw.get("page_type", ""),
        parent_path=raw.get("parent", ""),
        template_page_path=raw.get("template_page", ""),
        lookup_field=(raw.get("lookup_field", "pk") or "pk"),
        lookup_in=(raw.get("lookup_in", "path") or "path").lower(),
        publish_field=raw.get("publish_field", "") or "",
        title_source=raw.get("title_source", "title") or "title",
        slug_source=raw.get("slug_source", "slug") or "slug",
        on_delete=raw.get("on_delete", "page") or "page",
    )


def get_detail_pages(*, use_cache=True):
    global _detail_pages_cache
    if use_cache and _detail_pages_cache is not None:
        return _detail_pages_cache
    raw_config = getattr(settings, SETTING_NAME, {}) or {}
    pages = {}
    for key, raw in raw_config.items():
        if not isinstance(raw, dict):
            continue
        try:
            pages[key] = _build_detail_page(key, raw)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Invalid detail page config for %r", key)
    _detail_pages_cache = pages
    return pages


def reset_detail_pages():
    """Clear the cached registry (used by tests and ``override_settings``)."""
    global _detail_pages_cache
    _detail_pages_cache = None


def get_detail_page(key):
    return get_detail_pages().get(key)


def get_detail_page_keys():
    return list(get_detail_pages().keys())


def detail_page_for_instance(instance):
    """Return the ``DetailPageConfig`` whose model matches ``instance``."""
    if instance is None:
        return None
    model = type(instance)
    for config in get_detail_pages().values():
        candidate = config.model
        if candidate is not None and issubclass(model, candidate):
            return config
    return None
