"""Shared field layout primitives.

These blocks and builders describe how a field's parts (input, label, help and
error text) are arranged. They are intentionally pure: the builders return
Tailwind utility-class strings and the mixin only injects context, so every
input type can adopt them without changing its renderer.
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import (
    FIELD_PART_PLACEMENT_CHOICES,
    FIELD_PART_VISIBILITY_CHOICES,
)

from .compact import DaisieStructBlock
from .css import (
    build_design_css,
    build_layout_item_css,
    build_line_clamp_css,
    build_size_css,
)
from .form_layout import collapsed_group
from .layout_design import LayoutBlock, LayoutItemDesignBlock
from .size import BlockSizeBlock
from .utils import build_class


#: Field parts that may be independently laid out.
FIELD_PART_NAMES = ("input", "label", "help", "error")

#: Order utilities emitted for the high-level placement choices.
_PART_ORDER_CLASSES = {
    "start": "order-first",
    "middle": "order-none",
    "end": "order-last",
}

#: Default placement per part when the editor leaves ``placement`` on auto.
_DEFAULT_PART_PLACEMENTS = {
    "row": {"input": "start", "label": "middle", "help": "end"},
    "row-wrap": {"input": "start", "label": "middle", "help": "end"},
    "column": {"label": "start", "input": "middle", "help": "end"},
    "column-wrap": {"label": "start", "input": "middle", "help": "end"},
}


def _layout_choice(value):
    if not isinstance(value, dict):
        return ""
    return str(value.get("layout") or "")


def build_field_layout_css(value):
    """Container classes for a ``FieldLayoutBlock`` value."""
    return build_design_css((value or {}).get("layout"))


def build_field_group_css(value):
    """Container classes for a ``FieldGroupLayoutBlock`` value."""
    value = value or {}
    return build_class(
        build_design_css(value.get("layout")),
        build_size_css(value.get("size")),
    )


def build_field_group_context(value):
    """Flat template context for a ``FieldGroupLayoutBlock`` value."""
    css = build_field_group_css(value)
    return {
        "field_group_css": css,
        "field_group_configured": bool(css),
    }


def _is_grid(layout):
    return layout == "grid"


def build_field_part_css(value, *, layout="", part=""):
    """CSS classes for one field part.

    ``layout`` is the high-level layout choice of the enclosing field layout.
    ``part`` is the part name and controls whether ``max_lines`` is applied.
    """
    value = value or {}
    placement = str(value.get("placement") or "auto")
    if placement == "auto":
        placement = _DEFAULT_PART_PLACEMENTS.get(layout, {}).get(part, "auto")

    grid = _is_grid(layout) or placement == "grid"
    item = value.get("item")
    item_order = item.get("order") if isinstance(item, dict) else None
    order = ""
    if placement not in ("grid", "auto"):
        order = _PART_ORDER_CLASSES.get(placement, "")
    if item_order:
        order = ""

    max_lines = value.get("max_lines") if part in {"label", "help"} else None
    visibility = str(value.get("visibility") or "")

    return build_class(
        visibility,
        order,
        build_line_clamp_css(max_lines),
        build_layout_item_css(item, grid=grid),
    )


def build_field_part_context(value, *, layout="", part=""):
    """CSS and visibility flags for one field part."""
    visibility = str((value or {}).get("visibility") or "")
    return {
        "css": build_field_part_css(value, layout=layout, part=part),
        "hidden": visibility == "hidden",
        "sr_only": visibility == "sr-only",
    }


def build_field_layout_context(value):
    """Flat template context for a ``FieldLayoutBlock`` value."""
    value = value or {}
    layout_value = value.get("layout") or {}
    layout_choice = _layout_choice(layout_value)

    context = {
        "field_layout_css": build_field_layout_css(value),
        "field_layout_grid": layout_choice == "grid",
        "field_options_css": build_field_group_css(value.get("options")),
    }
    for part in FIELD_PART_NAMES:
        part_context = build_field_part_context(
            value.get(part), layout=layout_choice, part=part
        )
        context[f"field_{part}_css"] = part_context["css"]
        context[f"field_{part}_hidden"] = part_context["hidden"]
        context[f"field_{part}_sr_only"] = part_context["sr_only"]
    context["field_layout_configured"] = bool(
        context["field_layout_css"]
        or any(
            context[f"field_{part}_css"]
            or context[f"field_{part}_hidden"]
            or context[f"field_{part}_sr_only"]
            for part in FIELD_PART_NAMES
        )
    )
    return context


def build_field_option_context(value, *, layout=""):
    """CSS and visibility flags for a ``FieldOptionLayoutBlock`` value."""
    value = value or {}
    context = {}
    for part in ("input", "label"):
        part_context = build_field_part_context(
            value.get(part), layout=layout, part=part
        )
        context[f"option_{part}_css"] = part_context["css"]
        context[f"option_{part}_hidden"] = part_context["hidden"]
        context[f"option_{part}_sr_only"] = part_context["sr_only"]
    context["option_layout_configured"] = bool(
        any(
            context[f"option_{part}_css"]
            or context[f"option_{part}_hidden"]
            or context[f"option_{part}_sr_only"]
            for part in ("input", "label")
        )
    )
    return context


class FieldPartLayoutBlock(DaisieStructBlock):
    visibility = blocks.ChoiceBlock(
        choices=FIELD_PART_VISIBILITY_CHOICES,
        default="",
        required=False,
        label=_("Visibility"),
    )
    placement = blocks.ChoiceBlock(
        choices=FIELD_PART_PLACEMENT_CHOICES,
        default="auto",
        required=False,
        label=_("Placement"),
        help_text=_("Auto uses the default placement for the selected layout."),
    )
    max_lines = blocks.IntegerBlock(
        min_value=1,
        max_value=6,
        required=False,
        label=_("Maximum lines"),
        help_text=_("Clamp text to this many lines. Leave empty for no truncation."),
    )
    item = LayoutItemDesignBlock(
        required=False,
        label=_("Advanced layout"),
    )

    class Meta:
        icon = "sliders"
        label = _("Field part layout")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "visibility",
                "placement",
                "max_lines",
                collapsed_group(_("Advanced layout"), "item", icon="sliders"),
            ],
            heading=_("Field part layout"),
        )


class FieldGroupLayoutBlock(DaisieStructBlock):
    layout = LayoutBlock()
    size = BlockSizeBlock()

    class Meta:
        icon = "bars"
        label = _("Field group layout")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "layout",
                collapsed_group(_("Size and overflow"), "size", icon="expand-right"),
            ],
            heading=_("Field group layout"),
        )


class FieldOptionLayoutBlock(DaisieStructBlock):
    input = FieldPartLayoutBlock()
    label = FieldPartLayoutBlock()

    class Meta:
        icon = "radio-empty"
        label = _("Field option layout")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=["input", "label"],
            heading=_("Field option layout"),
        )


class FieldLayoutBlock(DaisieStructBlock):
    layout = LayoutBlock()
    input = FieldPartLayoutBlock()
    label = FieldPartLayoutBlock()
    help = FieldPartLayoutBlock()
    error = FieldPartLayoutBlock()
    options = FieldGroupLayoutBlock(
        required=False,
        label=_("Choice options"),
    )

    class Meta:
        icon = "sliders"
        label = _("Field layout")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "layout",
                "input",
                "label",
                "help",
                "error",
                collapsed_group(_("Choice options"), "options", icon="list-ul"),
            ],
            heading=_("Field layout"),
        )


class FieldLayoutMixin:
    """Expose field-part layout context for a block's ``field_layout`` value."""

    field_layout_key = "field_layout"

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        layout_value = (value or {}).get(self.field_layout_key) or {}
        context.update(build_field_layout_context(layout_value))
        return context


class FieldGroupLayoutMixin:
    """Expose group layout context for a block's ``group_layout`` value."""

    field_group_layout_key = "group_layout"

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        layout_value = (value or {}).get(self.field_group_layout_key) or {}
        context.update(build_field_group_context(layout_value))
        return context


class FieldOptionLayoutMixin:
    """Expose option layout context for a block's ``option_layout`` value."""

    field_option_layout_key = "option_layout"

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        layout_value = (value or {}).get(self.field_option_layout_key) or {}
        context.update(build_field_option_context(layout_value))
        return context
