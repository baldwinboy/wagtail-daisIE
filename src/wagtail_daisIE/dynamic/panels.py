"""Context models as email placeholder documentation.

The binding UI itself is self-documenting: each binding block shows an inline,
model-aware help panel (see ``dynamic/blocks.py`` and the admin JS adapter).
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _

from ..notifications.placeholders import register_placeholder_provider
from .registry import get_context_models


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
