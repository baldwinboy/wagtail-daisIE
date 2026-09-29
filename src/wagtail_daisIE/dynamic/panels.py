"""Context models as email placeholder documentation.

The binding UI itself is self-documenting: each binding block shows an inline,
model-aware help panel (see ``dynamic/blocks.py`` and the admin JS adapter).
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import HelpPanel

from ..notifications.placeholders import register_placeholder_provider
from .registry import get_context_model, get_context_models


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
        if config.url_source or config.supports_url:
            items.append(
                {
                    "token": f"{{{{ {key}.url }}}}",
                    "description": _("URL derived from the model's url_source."),
                }
            )
        for doc in config.field_docs(limit=12):
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


class FeedContextModelHelpPanel(HelpPanel):
    """List the properties available for a Feed's selected context model.

    Rendered as a ``<details>`` panel next to the Feed editor. It is
    server-rendered for the saved model and enhanced by
    ``wagtail_daisIE/js/feed_help.js`` so it updates immediately when the model
    select changes.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("template", "wagtail_daisIE/admin/feed_model_help.html")
        super().__init__(**kwargs)

    class BoundPanel(HelpPanel.BoundPanel):
        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            key = getattr(self.instance, "context_model", "") or ""
            config = get_context_model(key) if key else None
            model = config.model if config is not None else None
            context["feed_model"] = {
                "key": key,
                "label": str(config.label) if config else "",
                "model": model._meta.label if model else "",
                "summary": str(config.source_summary) if config else "",
                "examples": config.examples(limit=100) if config else [],
                "fields": config.field_docs(limit=None) if config else [],
                "filters": sorted(config.get_filters().keys()) if config else [],
            }
            return context
