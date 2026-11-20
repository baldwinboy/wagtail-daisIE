"""Context models as email placeholder documentation.

The binding UI itself is self-documenting: each binding block shows an inline,
model-aware help panel (see ``dynamic/blocks.py`` and the admin JS adapter).
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import HelpPanel

from ..notifications.placeholders import register_placeholder_provider
from .registry import get_context_models, get_context_models_help_state


def _context_model_placeholder_groups():
    groups = []
    for key, config in get_context_models().items():
        model = config.model
        items = [
            {
                "token": f"{{{{ {key} }}}}",
                "description": _("The resolved value, if any."),
            }
        ]
        for doc in config.help_fields(limit=12):
            items.append(
                {
                    "token": f"{{{{ {key}.{doc['name']} }}}}",
                    "description": doc["label"],
                }
            )
        groups.append(
            {
                "title": str(config.label),
                "description": model._meta.label if model else config.model_path,
                "items": items,
            }
        )
    return groups


# Register context models as placeholder documentation for every help panel.
register_placeholder_provider(_context_model_placeholder_groups)


def _bound_model_fields(feed):
    """Return every configured model and its metadata.

    Each entry carries ``active`` so the saved model's block renders visible and
    ``w-rules`` reveals another when the admin changes **context model**.
    """
    active_key = getattr(feed, "context_model", "") or ""
    help_state = get_context_models_help_state()
    models = []
    for key, model_state in help_state.items():
        active = key == active_key
        models.append(
            {
                "key": key,
                "label": model_state["label"],
                "model_label": model_state["model"],
                "summary": model_state["sourceSummary"],
                "examples": model_state["examples"] if active else [],
                "fields": model_state["helpFields"] if active else [],
                "filters": model_state["filters"] if active else [],
                "active": active,
            }
        )
    return {"key": active_key, "models": models}


class FeedContextModelHelpPanel(HelpPanel):
    """List the properties available for a Feed's selected context model.

    Rendered as a ``<details>`` panel next to the Feed editor. It is
    server-rendered for the saved model and enhanced by
    ``RulesController`` so it updates immediately when the model
    select changes.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("template", "wagtail_daisIE/admin/feed_model_help.html")
        super().__init__(**kwargs)

    class BoundPanel(HelpPanel.BoundPanel):
        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context["bound_model"] = _bound_model_fields(self.instance)
            return context
