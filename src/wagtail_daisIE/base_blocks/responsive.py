"""Responsive overrides for design blocks.

The stored value is a sparse list of breakpoint/utility pairs. Rendering only
needs to prefix each utility with its breakpoint, so this module has no
dependency on Django settings or the stylesheet build.
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices.responsive import (
    BREAKPOINT_ORDER,
    RESPONSIVE_BREAKPOINTS,
    RESPONSIVE_VALUE_CHOICES,
)
from wagtail_daisIE.widgets import DaisyUIResponsiveUtilityWidget

from .compact import DaisieStructBlock


class ResponsiveOverrideBlock(DaisieStructBlock):
    breakpoint = blocks.ChoiceBlock(
        choices=RESPONSIVE_BREAKPOINTS,
        default="md",
        label=_("Breakpoint"),
    )
    value = blocks.ChoiceBlock(
        choices=RESPONSIVE_VALUE_CHOICES,
        label=_("Utility"),
        widget=DaisyUIResponsiveUtilityWidget(),
    )

    class Meta:
        icon = "sliders"
        label = _("Design")


def responsive_overrides():
    """Return a fresh responsive-design list block.

    A new ``ListBlock`` (and child block) is created per call so design blocks
    never share mutable block instances.
    """
    return blocks.ListBlock(
        ResponsiveOverrideBlock(),
        label=_("Responsive design"),
        default=[],
    )


def build_responsive_css(overrides):
    """Return ``md:p-8 lg:text-2xl`` for a stored overrides list."""
    if not overrides:
        return ""

    ordered = sorted(
        (
            item
            for item in overrides
            if isinstance(item, dict) and item.get("breakpoint") and item.get("value")
        ),
        key=lambda item: BREAKPOINT_ORDER.get(
            item["breakpoint"], len(BREAKPOINT_ORDER)
        ),
    )

    classes = []
    seen = set()
    for item in ordered:
        key = (item["breakpoint"], item["value"])
        if key in seen:
            continue
        seen.add(key)
        classes.append(f"{item['breakpoint']}:{item['value']}")
    return " ".join(classes)
