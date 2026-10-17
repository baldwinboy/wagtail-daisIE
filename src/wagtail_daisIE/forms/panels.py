"""Admin help panel describing the fields of a form page's bound model."""

from __future__ import annotations

from wagtail.admin.panels import HelpPanel

from ..dynamic.registry import get_context_models


def _bound_model_fields(page):
    """Return every configured model and its editable fields.

    Each entry carries ``active`` so the saved model's block renders visible and
    ``w-rules`` reveals another when the admin changes **Model to create**.
    """
    active_key = getattr(page, "instance_model", "") or ""
    models = []
    for key, config in get_context_models().items():
        model = config.model
        models.append(
            {
                "key": key,
                "label": str(config.label),
                "model_label": model._meta.label if model is not None else "",
                "fields": config.form_fields(),
                "active": key == active_key,
            }
        )
    return {"key": active_key, "models": models}


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
            context["bound_model"] = _bound_model_fields(self.instance)
            return context
