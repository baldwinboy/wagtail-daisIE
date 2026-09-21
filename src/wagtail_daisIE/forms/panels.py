"""Admin help panel describing the fields of a form page's bound model."""

from __future__ import annotations

from wagtail.admin.panels import HelpPanel

from ..dynamic.registry import get_context_model


def bound_model_fields(page):
    """Return the editable fields of the model bound to ``page``."""
    key = getattr(page, "instance_model", "") or ""
    config = get_context_model(key) if key else None
    model = config.model if config is not None else None

    fields = []
    if model is not None:
        for model_field in model._meta.get_fields():
            if not getattr(model_field, "editable", False):
                continue
            if not getattr(model_field, "concrete", False) and not getattr(
                model_field, "many_to_many", False
            ):
                continue
            try:
                field_type = model_field.get_internal_type()
            except Exception:  # pragma: no cover - defensive
                field_type = "ManyToManyField"
            fields.append(
                {
                    "name": model_field.name,
                    "label": str(
                        getattr(model_field, "verbose_name", model_field.name)
                        or model_field.name
                    ),
                    "type": field_type,
                }
            )

    return {
        "key": key,
        "label": model._meta.label if model is not None else "",
        "fields": fields,
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
