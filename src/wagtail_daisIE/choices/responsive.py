"""Responsive utility vocabulary and the admin editor schema.

The admin stores a sparse list of ``{breakpoint, value}`` overrides. This module
is the single source of truth for the breakpoints, the four-widget editor
(design area -> property -> side -> value) and the responsive safelist.
"""

from __future__ import annotations

from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from .alignment import ALIGNMENT_CHOICES, JUSTIFY_CHOICES
from .components import FLEX_WRAP_CHOICES
from .size import (
    BLOCK_HEIGHT_CHOICES,
    BLOCK_MAX_HEIGHT_CHOICES,
    BLOCK_MAX_WIDTH_CHOICES,
    BLOCK_MIN_HEIGHT_CHOICES,
    BLOCK_MIN_WIDTH_CHOICES,
    BLOCK_SIZE_CHOICES,
    BLOCK_WIDTH_CHOICES,
)
from .spacing import (
    GAP_ALL_CHOICES,
    GAP_HORIZONTAL_CHOICES,
    GAP_VERTICAL_CHOICES,
    MARGIN_ALL_CHOICES,
    MARGIN_BOTTOM_CHOICES,
    MARGIN_LEFT_CHOICES,
    MARGIN_RIGHT_CHOICES,
    MARGIN_TOP_CHOICES,
    PADDING_ALL_CHOICES,
    PADDING_BOTTOM_CHOICES,
    PADDING_LEFT_CHOICES,
    PADDING_RIGHT_CHOICES,
    PADDING_TOP_CHOICES,
)
from .typography import (
    FONT_SIZE_CHOICES,
    FONT_WEIGHT_CHOICES,
    LETTER_SPACING_CHOICES,
    LINE_HEIGHT_CHOICES,
    TEXT_ALIGN_CHOICES,
)
from .utils import ChoiceList


RESPONSIVE_BREAKPOINTS = ChoiceList(
    [
        ("sm", _("Mobile (640px and up)")),
        ("md", _("Tablet (768px and up)")),
        ("lg", _("Desktop (1024px and up)")),
    ],
    "RESPONSIVE_BREAKPOINTS",
)

#: Breakpoint key -> sort position.
BREAKPOINT_ORDER = {
    value: index for index, (value, _label) in enumerate(RESPONSIVE_BREAKPOINTS)
}

#: Side keys shared by the editor and the schema.
RESPONSIVE_SIDES = (
    ("all", _("All")),
    ("top", _("Top")),
    ("right", _("Right")),
    ("bottom", _("Bottom")),
    ("left", _("Left")),
    ("horizontal", _("Horizontal")),
    ("vertical", _("Vertical")),
)


def _options(choice_list):
    """Return ``(value, label)`` pairs, keeping the empty "None" option."""
    return [
        (
            value,
            format_lazy("{label} — {value}", label=label, value=value)
            if value
            else label,
        )
        for value, label in choice_list
    ]


def _simple(key, label, choices, widget):
    return {
        "key": key,
        "label": label,
        "widget": widget,
        "has_sides": False,
        "sides": (("all", _("All"), choices),),
    }


def _sided(key, label, sides, widget="slider"):
    return {
        "key": key,
        "label": label,
        "widget": widget,
        "has_sides": True,
        "sides": sides,
    }


_LAYOUT_DISPLAY = [
    ("block", _("Block")),
    ("inline-block", _("Inline block")),
    ("flex", _("Flex")),
    ("grid", _("Grid")),
    ("hidden", _("Hidden")),
]

_LAYOUT_JUSTIFY = [
    (value, label) for value, label in JUSTIFY_CHOICES if value.startswith("justify-")
]

_LAYOUT_COLUMNS = [
    (f"grid-cols-{count}", format_lazy("{count} columns", count=count))
    for count in range(1, 7)
]

#: The admin editor schema: design area -> property -> side -> choices.
RESPONSIVE_DESIGN_AREAS = (
    {
        "key": "typography",
        "label": _("Typography"),
        "properties": (
            _simple("font_size", _("Font size"), FONT_SIZE_CHOICES, "slider"),
            _simple("font_weight", _("Font weight"), FONT_WEIGHT_CHOICES, "slider"),
            _simple("line_height", _("Line height"), LINE_HEIGHT_CHOICES, "slider"),
            _simple(
                "letter_spacing",
                _("Letter spacing"),
                LETTER_SPACING_CHOICES,
                "slider",
            ),
            _simple("text_align", _("Text align"), TEXT_ALIGN_CHOICES, "select"),
        ),
    },
    {
        "key": "spacing",
        "label": _("Spacing"),
        "properties": (
            _sided(
                "padding",
                _("Padding"),
                (
                    ("all", _("All"), PADDING_ALL_CHOICES),
                    ("top", _("Top"), PADDING_TOP_CHOICES),
                    ("right", _("Right"), PADDING_RIGHT_CHOICES),
                    ("bottom", _("Bottom"), PADDING_BOTTOM_CHOICES),
                    ("left", _("Left"), PADDING_LEFT_CHOICES),
                ),
            ),
            _sided(
                "margin",
                _("Margin"),
                (
                    ("all", _("All"), MARGIN_ALL_CHOICES),
                    ("top", _("Top"), MARGIN_TOP_CHOICES),
                    ("right", _("Right"), MARGIN_RIGHT_CHOICES),
                    ("bottom", _("Bottom"), MARGIN_BOTTOM_CHOICES),
                    ("left", _("Left"), MARGIN_LEFT_CHOICES),
                ),
            ),
            _sided(
                "gap",
                _("Spacing"),
                (
                    ("all", _("All"), GAP_ALL_CHOICES),
                    ("horizontal", _("Horizontal"), GAP_HORIZONTAL_CHOICES),
                    ("vertical", _("Vertical"), GAP_VERTICAL_CHOICES),
                ),
            ),
        ),
    },
    {
        "key": "size",
        "label": _("Size"),
        "properties": (
            _simple("width", _("Width"), BLOCK_WIDTH_CHOICES, "slider"),
            _simple("min_width", _("Min width"), BLOCK_MIN_WIDTH_CHOICES, "slider"),
            _simple("max_width", _("Max width"), BLOCK_MAX_WIDTH_CHOICES, "slider"),
            _simple("height", _("Height"), BLOCK_HEIGHT_CHOICES, "slider"),
            _simple("min_height", _("Min height"), BLOCK_MIN_HEIGHT_CHOICES, "slider"),
            _simple("max_height", _("Max height"), BLOCK_MAX_HEIGHT_CHOICES, "slider"),
            _simple("size", _("Size"), BLOCK_SIZE_CHOICES, "slider"),
        ),
    },
    {
        "key": "layout",
        "label": _("Layout"),
        "properties": (
            _simple("display", _("Display"), _LAYOUT_DISPLAY, "select"),
            _simple("wrap", _("Wrap"), FLEX_WRAP_CHOICES, "select"),
            _simple("justify", _("Justify"), _LAYOUT_JUSTIFY, "select"),
            _simple("align", _("Align"), ALIGNMENT_CHOICES, "select"),
            _simple("columns", _("Columns"), _LAYOUT_COLUMNS, "select"),
        ),
    },
)


def _build_schema(areas):
    """Return ``(meta, grouped_choices, groups_by_key)``."""
    meta = {}
    groups = []
    groups_by_key = {}

    for area in areas:
        for prop in area["properties"]:
            for side_key, side_label, choices in prop["sides"]:
                options = _options(choices)
                group_label = (
                    format_lazy(
                        "{property} — {side}",
                        property=prop["label"],
                        side=side_label,
                    )
                    if prop["has_sides"]
                    else prop["label"]
                )
                groups.append((group_label, options))
                groups_by_key[(area["key"], prop["key"], side_key)] = (
                    group_label,
                    options,
                )
                for value, _label in options:
                    if value:
                        meta[value] = (area["key"], prop["key"], side_key)

    return meta, groups, groups_by_key


(
    RESPONSIVE_UTILITY_META,
    _RESPONSIVE_GROUPS,
    RESPONSIVE_GROUPS_BY_KEY,
) = _build_schema(RESPONSIVE_DESIGN_AREAS)

#: Grouped choices for the ``ChoiceBlock`` (validation and no-JS fallback).
RESPONSIVE_VALUE_CHOICES = ChoiceList(
    _RESPONSIVE_GROUPS,
    "RESPONSIVE_VALUE_CHOICES",
)

#: Every utility the editor can produce.
RESPONSIVE_CLASSES = frozenset(RESPONSIVE_UTILITY_META)
