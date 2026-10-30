"""Validation for ``WAGTAIL_DAISIE_DETAIL_PAGES`` configurations."""

from __future__ import annotations

from wagtail.models import Page

from .exceptions import DetailPageConfigurationError
from .models import GeneratedPagesIndexPage, ModelDetailPage, ModelDetailTemplate
from .registry import get_detail_pages


def _require_subclass(model, parent, *, key, label):
    if model is None:
        raise DetailPageConfigurationError(
            f"Detail type {key!r} has no {label} configured."
        )
    if not isinstance(model, type) or not issubclass(model, parent):
        raise DetailPageConfigurationError(
            f"Detail type {key!r}: {label} must subclass {parent.__name__}."
        )


def validate_config(config):
    """Validate one detail-page configuration without querying the database."""
    _require_subclass(
        config.page_type, ModelDetailPage, key=config.key, label="page_type"
    )
    _require_subclass(
        config.template_page_model,
        ModelDetailTemplate,
        key=config.key,
        label="template_page",
    )
    _require_subclass(
        config.generated_index_model,
        GeneratedPagesIndexPage,
        key=config.key,
        label="generated_index",
    )
    _require_subclass(config.parent_model, Page, key=config.key, label="parent")


def validate_records(config):
    """Validate the page records required by one configuration."""
    config.get_template_page()
    generated_index = config.get_generated_index_page()

    parent_model = config.parent_model
    if parent_model is not None:
        pages = parent_model.objects.all()
        if pages.count() != 1:
            raise DetailPageConfigurationError(
                f"Detail type {config.key!r} needs exactly one index page; "
                f"found {pages.count()}."
            )
        listing = pages.first()
        if not listing.live:
            raise DetailPageConfigurationError(
                f"Index page for detail type {config.key!r} is not live."
            )
        if generated_index.get_parent().pk != listing.pk:
            raise DetailPageConfigurationError(
                f"Generated index for detail type {config.key!r} is not under "
                f"its index page."
            )


def validate_detail_pages(configs=None, *, records=True):
    """Validate every configured detail page, raising on the first failure."""
    configs = get_detail_pages().values() if configs is None else configs
    for config in configs:
        validate_config(config)
        if records:
            validate_records(config)


__all__ = [
    "DetailPageConfigurationError",
    "validate_config",
    "validate_detail_pages",
    "validate_records",
]
