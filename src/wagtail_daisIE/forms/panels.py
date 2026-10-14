"""Admin help panel describing the fields of a form page's bound model."""

from __future__ import annotations

import json

from wagtail.admin.panels import FieldPanel, HelpPanel

from ..dynamic.registry import get_context_models


def bound_model_fields(page):
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
            context["bound_model"] = bound_model_fields(self.instance)
            return context


class PrefixedRulesPanel(FieldPanel):
    """A ``FieldPanel`` revealed when another field has one of ``rules``.

    ``rules`` maps a field on the same (possibly prefixed) form to the values
    that reveal this panel. The dependency's HTML name is resolved when the
    panel is bound — e.g. ``form_fields-0-field_type`` inside an ``InlinePanel``
    formset — and written into a ``data-w-rules`` attribute for Wagtail's
    ``w-rules`` controller.
    """

    def __init__(self, field_name, rules=None, *, match="any", **kwargs):
        self.rules = {key: list(values) for key, values in (rules or {}).items()}
        self.match = match
        super().__init__(field_name, **kwargs)

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs.update(rules=self.rules, match=self.match)
        return kwargs

    class BoundPanel(FieldPanel.BoundPanel):
        @property
        def attrs(self):
            attrs = dict(self.panel.attrs)
            rules = self._prefixed_rules()
            if rules:
                attrs["data-w-rules-target"] = "show"
                attrs["data-w-rules"] = json.dumps(rules)
                attrs["data-w-rules-match"] = self.panel.match
                if not self._matches():
                    attrs["hidden"] = True
            return attrs

        def _prefixed_rules(self):
            if self.form is None:
                return {}
            resolve = (
                self.form.add_prefix
                if getattr(self.form, "prefix", "")
                else (lambda name: name)
            )
            return {resolve(name): values for name, values in self.panel.rules.items()}

        def _matches(self):
            results = []
            for name, values in self.panel.rules.items():
                field = self.form[name] if name in self.form.fields else None
                if field is None:
                    results.append(False)
                    continue
                current = field.value()
                if isinstance(current, (list, tuple)):
                    results.append(any(str(item) in values for item in current))
                else:
                    results.append(str(current or "") in values)
            if not results:
                return True
            return all(results) if self.panel.match == "all" else any(results)
