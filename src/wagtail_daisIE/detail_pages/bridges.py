"""Create, update and delete detail pages from model signals."""

from __future__ import annotations

import logging

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_delete
from wagtail.coreutils import find_available_slug, slugify

from .exceptions import DetailPageConfigurationError
from .registry import get_detail_pages


logger = logging.getLogger(__name__)


def _dispatch_uid(config, suffix):
    return f"wagtail_daisIE.detail.{suffix}.{config.key}"


def find_detail_page(config, instance):
    """Return the detail page bound to ``instance``, or ``None``."""
    page_type = config.page_type
    if page_type is None or instance is None or instance.pk is None:
        return None
    content_type = ContentType.objects.get_for_model(type(instance))
    return page_type.objects.filter(
        detail_key=config.key,
        source_content_type=content_type,
        source_object_id=instance.pk,
    ).first()


def _apply_fields(page, config, instance, parent=None):
    page.title = str(getattr(instance, config.title_source, "") or page.title)
    if parent is None:
        parent = page.get_parent()
    raw_slug = str(getattr(instance, config.slug_source, "") or "")
    requested = slugify(raw_slug) or page.slug
    if parent is not None:
        listing = parent.get_parent()
        if listing is not None:
            collision = (
                listing.get_children()
                .filter(slug=requested)
                .exclude(pk=page.pk)
                .exists()
            )
            if collision:
                raise DetailPageConfigurationError(
                    f"Detail slug {requested!r} collides with a child of {listing!r}."
                )
        page.slug = find_available_slug(parent, requested, ignore_page_id=page.pk)
    else:
        page.slug = requested
    page.detail_key = config.key
    page.source_content_type = ContentType.objects.get_for_model(type(instance))
    page.source_object_id = instance.pk
    return page


def sync_detail_page(config, instance, *, created=False):
    """Create, refresh or delete the detail page for ``instance``."""
    page_type = config.page_type
    if page_type is None or instance.pk is None:
        return None

    publish = not config.publish_field or bool(
        getattr(instance, config.publish_field, False)
    )
    page = find_detail_page(config, instance)

    # Non-public entities have no generated page at all.
    if not publish:
        if page is not None:
            page.delete()
        return None

    # Both lookups are exact and raise DetailPageConfigurationError.
    config.get_template_page()
    parent = config.get_generated_index_page()

    if page is None:
        page = page_type(title=str(instance), slug="")
        page.live = False
        page = _apply_fields(page, config, instance, parent)
        parent.add_child(instance=page)
    else:
        page = page.specific
        if page.get_parent().pk != parent.pk:
            page.move(parent, pos="last-child")
        page = _apply_fields(page, config, instance, parent)
        page.save()

    page.save_revision().publish()
    return page


def delete_detail_page(config, instance):
    """Delete or unlink the detail page for ``instance``."""
    page = find_detail_page(config, instance)
    if page is None:
        return
    if config.on_delete == "ignore":
        return
    if config.on_delete == "unlink":
        specific = page.specific
        specific.source_content_type = None
        specific.source_object_id = None
        specific.save()
        specific.save_revision().publish()
        return
    page.delete()


def make_save_receiver(config):
    def receiver(sender, instance, **kwargs):
        try:
            sync_detail_page(config, instance, created=kwargs.get("created", False))
        except DetailPageConfigurationError:
            logger.exception("Detail page configuration failed for %r", config.key)
            raise
        except Exception:
            logger.exception("Detail page sync failed for %r", config.key)

    receiver.__name__ = f"daisie_detail_save_{config.key}"
    return receiver


def make_delete_receiver(config):
    def receiver(sender, instance, **kwargs):
        try:
            delete_detail_page(config, instance)
        except Exception:
            logger.exception("Detail page delete failed for %r", config.key)

    receiver.__name__ = f"daisie_detail_delete_{config.key}"
    return receiver


def connect_signals():
    """Connect a create/update and delete receiver per configured type."""
    connected = 0
    for config in get_detail_pages().values():
        model = config.model
        if model is None or config.page_type is None:
            continue
        post_save.connect(
            make_save_receiver(config),
            sender=model,
            dispatch_uid=_dispatch_uid(config, "save"),
            weak=False,
        )
        pre_delete.connect(
            make_delete_receiver(config),
            sender=model,
            dispatch_uid=_dispatch_uid(config, "delete"),
            weak=False,
        )
        connected += 2
    return connected


def disconnect_signals():
    """Disconnect every detail-page receiver (used by tests/reloads)."""
    for config in get_detail_pages().values():
        model = config.model
        if model is None:
            continue
        post_save.disconnect(sender=model, dispatch_uid=_dispatch_uid(config, "save"))
        pre_delete.disconnect(
            sender=model, dispatch_uid=_dispatch_uid(config, "delete")
        )
