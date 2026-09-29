"""Run approval workflows when a model's approval field turns true."""

from __future__ import annotations

import logging

from django.db.models.signals import post_save, pre_save

from .registry import get_workflows


logger = logging.getLogger(__name__)

PREV_ATTR = "_daisie_prev_approval"


def _dispatch_uid(workflow, suffix):
    return f"wagtail_daisIE.approval.{suffix}.{workflow.key}"


def make_pre_save_receiver(workflow):
    def receiver(sender, instance, **kwargs):
        if instance.pk is None:
            setattr(instance, PREV_ATTR, None)
            return
        try:
            old = (
                sender._default_manager.filter(pk=instance.pk)
                .values_list(workflow.approval_field, flat=True)
                .first()
            )
        except Exception:  # pragma: no cover - defensive
            old = None
        setattr(instance, PREV_ATTR, old)

    receiver.__name__ = f"daisie_approval_presave_{workflow.key}"
    return receiver


def make_save_receiver(workflow):
    def receiver(sender, instance, **kwargs):
        if not bool(getattr(instance, workflow.approval_field, False)):
            return
        if getattr(instance, PREV_ATTR, None) is True:
            return
        if workflow.converted_field and getattr(
            instance, workflow.converted_field, None
        ):
            return
        handler = workflow.handler
        if handler is None:
            return
        try:
            result = handler(instance)
        except Exception:
            logger.exception("Approval workflow %r handler failed", workflow.key)
            return
        if result is None or not workflow.converted_field:
            return
        try:
            sender._default_manager.filter(pk=instance.pk).update(
                **{workflow.converted_field: result}
            )
        except Exception:
            logger.exception("Could not record converted value for %r", workflow.key)
            return
        setattr(instance, workflow.converted_field, result)

    receiver.__name__ = f"daisie_approval_save_{workflow.key}"
    return receiver


def connect_signals():
    connected = 0
    for workflow in get_workflows().values():
        model = workflow.model
        if model is None or not workflow.handler_path:
            continue
        pre_save.connect(
            make_pre_save_receiver(workflow),
            sender=model,
            dispatch_uid=_dispatch_uid(workflow, "presave"),
            weak=False,
        )
        post_save.connect(
            make_save_receiver(workflow),
            sender=model,
            dispatch_uid=_dispatch_uid(workflow, "save"),
            weak=False,
        )
        connected += 2
    return connected


def disconnect_signals():
    for workflow in get_workflows().values():
        model = workflow.model
        if model is None:
            continue
        pre_save.disconnect(
            sender=model, dispatch_uid=_dispatch_uid(workflow, "presave")
        )
        post_save.disconnect(sender=model, dispatch_uid=_dispatch_uid(workflow, "save"))
