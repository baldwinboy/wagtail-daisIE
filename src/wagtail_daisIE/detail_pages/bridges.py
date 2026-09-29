"""Create, update and delete detail pages from model signals."""

from __future__ import annotations

import logging

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_delete
from wagtail.coreutils import find_available_slug, slugify
from wagtail.models import Page

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


def _template_page(config):
    model = config.template_page_model
    if model is None:
        return None
    return model.objects.live().first() or model.objects.first()


def _parent_page(config):
    template = _template_page(config)
    chosen = getattr(template, "parent_page", None) if template is not None else None
    if chosen is not None:
        return chosen
    model = config.parent_model
    if model is not None:
        page = model.objects.live().first() or model.objects.first()
        if page is not None:
            return page
    return Page.objects.filter(depth=2).first()


def _apply_fields(page, config, instance, parent=None):
    page.title = str(getattr(instance, config.title_source, "") or page.title)
    if parent is None:
        parent = page.get_parent()
    raw_slug = str(getattr(instance, config.slug_source, "") or "")
    requested = slugify(raw_slug) or page.slug
    if parent is not None:
        page.slug = find_available_slug(parent, requested, ignore_page_id=page.pk)
    else:
        page.slug = requested
    page.detail_key = config.key
    page.source_content_type = ContentType.objects.get_for_model(type(instance))
    page.source_object_id = instance.pk
    if page.design_template_id is None:
        page.design_template = _template_page(config)
    return page


def sync_detail_page(config, instance, *, created=False):
    """Create or refresh the detail page for ``instance``."""
    page_type = config.page_type
    if page_type is None or instance.pk is None:
        return None

    page = find_detail_page(config, instance)
    if page is None:
        parent = _parent_page(config)
        if parent is None:
            logger.warning("No parent page for detail type %r", config.key)
            return None
        page = page_type(title=str(instance), slug="")
        page.live = False
        page = _apply_fields(page, config, instance, parent)
        parent.add_child(instance=page)
    else:
        page = page.specific
        page = _apply_fields(page, config, instance)
        page.save()

    publish = not config.publish_field or bool(
        getattr(instance, config.publish_field, False)
    )
    if publish:
        page.save_revision().publish()
    else:
        page.save_revision()
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
