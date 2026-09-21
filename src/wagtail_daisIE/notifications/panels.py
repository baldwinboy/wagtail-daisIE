"""Admin panels that document available placeholder variables."""

from __future__ import annotations

from wagtail.admin.panels import HelpPanel

from .placeholders import get_placeholder_groups


class EmailPlaceholdersHelpPanel(HelpPanel):
    """Help panel listing the placeholders available in email templates.

    The panel is intentionally read-only and self-documenting: bridge and
    integration placeholders appear automatically via
    :func:`wagtail_daisIE.notifications.placeholders.register_placeholder_provider`.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault(
            "template",
            "wagtail_daisIE/admin/email_placeholders_help.html",
        )
        super().__init__(**kwargs)

    class BoundPanel(HelpPanel.BoundPanel):
        def get_context_data(self, parent_context=None):
            context = super().get_context_data(parent_context)
            context["placeholder_groups"] = get_placeholder_groups()
            return context
