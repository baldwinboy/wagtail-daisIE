"""Registry of approval workflows.

Projects declare, in settings, which models convert once approved::

    WAGTAIL_DAISIE_APPROVAL_WORKFLOWS = {
        "bread_suggestion": {
            "label": _("Bread suggestion"),
            "model": "blog.BreadSuggestion",
            "approval_field": "is_approved",
            "handler": "blog.workflows.approve_bread_suggestion",
            "converted_field": "bread",
        },
    }

Nothing here touches the database at import time.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass, field

from django.utils.module_loading import import_string

from ..dynamic.registry import resolve_model
from .conf import get_workflow_config


logger = logging.getLogger(__name__)

_workflows_cache: dict[str, ApprovalWorkflow] | None = None


@dataclass
class ApprovalWorkflow:
    key: str
    label: object
    model_path: str = ""
    approval_field: str = "is_approved"
    handler_path: str = ""
    converted_field: str = ""
    _resolved_model: object = field(default=None, repr=False)
    _resolved_handler: object = field(default=None, repr=False)

    def __str__(self):
        return str(self.label or self.key)

    @property
    def model(self):
        if self._resolved_model is None:
            self._resolved_model = resolve_model(self.model_path)
        return self._resolved_model

    @property
    def handler(self):
        if self._resolved_handler is None and self.handler_path:
            try:
                self._resolved_handler = import_string(self.handler_path)
            except ImportError:
                logger.warning(
                    "Could not resolve approval handler %r", self.handler_path
                )
        return self._resolved_handler


def _build_workflow(key, raw):
    raw = dict(raw or {})
    return ApprovalWorkflow(
        key=key,
        label=raw.get("label") or key.replace("_", " ").title(),
        model_path=raw.get("model", "") or "",
        approval_field=raw.get("approval_field", "is_approved") or "is_approved",
        handler_path=raw.get("handler", "") or "",
        converted_field=raw.get("converted_field", "") or "",
    )


def get_workflows():
    global _workflows_cache
    if _workflows_cache is not None:
        return _workflows_cache
    workflows = {}
    for key, raw in get_workflow_config().items():
        if not isinstance(raw, dict):
            continue
        try:
            workflows[key] = _build_workflow(key, raw)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Invalid approval workflow config for %r", key)
    _workflows_cache = workflows
    return workflows


def reset_workflows():
    global _workflows_cache
    _workflows_cache = None


def workflow_for_instance(instance):
    if instance is None:
        return None
    model = type(instance)
    for workflow in get_workflows().values():
        candidate = workflow.model
        if candidate is not None and issubclass(model, candidate):
            return workflow
    return None
