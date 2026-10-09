"""Admin help panel describing the fields of a form page's bound model."""

from __future__ import annotations

from wagtail.admin.panels import HelpPanel

from ..dynamic.registry import get_context_model


def bound_model_fields(page):
    """Return the editable fields of the model bound to ``page``."""
    key = getattr(page, "instance_model", "") or ""
    config = get_context_model(key) if key else None
    model = config.model if config is not None else None
    return {
        "key": key,
        "label": model._meta.label if model is not None else "",
        "fields": config.form_fields() if config is not None else [],
    }


class FormModelFieldsHelpPanel(HelpPanel):
    """List the fields an admin can link form inputs to."""

    def __init__(self, **kwargs):
        kwargs.setdefault(
            "template",
            "wagtail_daisIE/admin/form_model_fields_help.html",
        )
        super().__init__(**kwargs)

    class BoundPanel(HelpPanel.BoundPanel):
        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context["bound_model"] = bound_model_fields(self.instance)
            return context
