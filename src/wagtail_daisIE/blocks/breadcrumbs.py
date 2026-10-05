"""DaisyUI breadcrumbs as a placeable block.

By default the block resolves the current page from the render context, so it
can be dropped into any page / form page body and shows the page and its
parents. Inside an allauth page override there is no Wagtail page tree, so it
falls back to the override's view label.

Authors who want full control can add explicit ``items``; when any are present
they replace the automatic trail entirely (each item has its own label, link
and icon).
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks import ThemedTypographyBlock
from ..base_blocks.compact import DaisieStructBlock
from ..base_blocks.link import LinkDestinationBlock, link_url
from ..icons.blocks import IconChooserBlock


class BreadcrumbItemBlock(DaisieStructBlock):
    """One manually authored crumb."""

    label = blocks.CharBlock(max_length=255)
    destination = LinkDestinationBlock()
    icon = IconChooserBlock(required=False)

    class Meta:
        icon = "link"
        label = _("Crumb")
        collapsed = True


class BreadcrumbsBlock(ThemedTypographyBlock):
    items = blocks.ListBlock(
        BreadcrumbItemBlock(),
        required=False,
        label=_("Crumbs"),
        help_text=_(
            "Optional. When set, these replace the automatic page breadcrumbs, "
            "giving full control over every crumb."
        ),
    )
    icon = IconChooserBlock(
        required=False,
        help_text=_("Automatic mode: shown before each crumb."),
    )
    home_icon = IconChooserBlock(
        required=False,
        help_text=_("Automatic mode: overrides the icon for the first crumb."),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        parent_context = parent_context or {}
        value = value or {}

        items = value.get("items") or []
        crumbs = []
        if items:
            for item in items:
                crumbs.append(
                    {
                        "label": item.get("label", ""),
                        "url": link_url(item.get("destination"), context=context),
                        "icon": item.get("icon"),
                    }
                )
        else:
            crumbs = self._auto_crumbs(value, parent_context, context)

        context["crumbs"] = crumbs
        return context

    def _auto_crumbs(self, value, parent_context, context):
        from wagtail.models import Page

        default_icon = value.get("icon")
        home_icon = value.get("home_icon") or default_icon

        page = parent_context.get("page") or parent_context.get("self")
        if page is not None and getattr(page, "depth", 0) > 2:
            ancestors = list(
                Page.objects.ancestor_of(page, inclusive=True).filter(depth__gt=1)
            )
            last = len(ancestors) - 1
            return [
                {
                    "label": _("Home") if index == 0 else str(ancestor),
                    "url": "" if index == last else ancestor.get_url(),
                    "icon": home_icon if index == 0 else default_icon,
                }
                for index, ancestor in enumerate(ancestors)
            ]

        override = parent_context.get("override")
        label = ""
        if override is not None:
            try:
                label = str(override.get_view_display() or "")
            except Exception:
                label = ""
        if label:
            return [{"label": label, "url": "", "icon": default_icon}]
        return []

    class Meta:
        icon = "arrow-right"
        group = _("Navigation")
        collapsed = True
        template = "wagtail_daisIE/blocks/breadcrumbs.html"
        form_layout = blocks.BlockGroup(
            children=["items", "icon", "home_icon"],
            settings=["design", "audience"],
        )


__all__ = ["BreadcrumbItemBlock", "BreadcrumbsBlock"]
