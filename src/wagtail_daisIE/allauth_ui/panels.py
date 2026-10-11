"""Admin help panels for the allauth page designer."""

from __future__ import annotations

from wagtail.admin.panels import HelpPanel


class InlineMarkupHelpPanel(HelpPanel):
    """Static reference for the inline markup accepted in label/help fields."""

    def __init__(self, **kwargs):
        kwargs.setdefault(
            "template",
            "wagtail_daisIE/admin/inline_markup_help.html",
        )
        super().__init__(**kwargs)
