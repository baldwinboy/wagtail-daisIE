"""DaisyUI data-input component blocks.

Editors use these to design the look of inputs, including error and helper
states. They render the same markup the form builder produces, so a designed
form and a form page stay visually consistent.
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks import ThemedBlock
from ..choices.inputs import (
    CHOICE_COLOR_CHOICES,
    CHOICE_SIZE_CHOICES,
    FILE_COLOR_CHOICES,
    FILE_SIZE_CHOICES,
    INPUT_COLOR_CHOICES,
    INPUT_SIZE_CHOICES,
    INPUT_TYPE_CHOICES,
    RADIO_COLOR_CHOICES,
    RADIO_SIZE_CHOICES,
    RANGE_COLOR_CHOICES,
    RANGE_SIZE_CHOICES,
    RATING_SIZE_CHOICES,
    SELECT_COLOR_CHOICES,
    SELECT_SIZE_CHOICES,
    TEXTAREA_COLOR_CHOICES,
    TEXTAREA_SIZE_CHOICES,
    TOGGLE_COLOR_CHOICES,
    TOGGLE_SIZE_CHOICES,
)


def _split_options(value):
    if not value:
        return []
    text = str(value)
    if "\n" in text:
        return [line.strip() for line in text.splitlines() if line.strip()]
    return [item.strip() for item in text.split(",") if item.strip()]


class InputBlock(ThemedBlock):
    label = blocks.CharBlock(max_length=255, label=_("Label"))
    name = blocks.CharBlock(
        max_length=64, required=False, blank=True, label=_("Field name")
    )
    input_type = blocks.ChoiceBlock(
        choices=INPUT_TYPE_CHOICES, default="text", label=_("Input type")
    )
    placeholder = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Placeholder")
    )
    value = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Default value")
    )
    color = blocks.ChoiceBlock(
        choices=INPUT_COLOR_CHOICES, required=False, label=_("Colour")
    )
    size = blocks.ChoiceBlock(
        choices=INPUT_SIZE_CHOICES, required=False, label=_("Size")
    )
    required = blocks.BooleanBlock(default=False, required=False, label=_("Required"))
    helper_text = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Helper text")
    )
    error_text = blocks.CharBlock(
        max_length=255,
        required=False,
        blank=True,
        label=_("Error message"),
        help_text=_("Shows the error state."),
    )

    class Meta:
        icon = "edit"
        group = _("Data input")
        collapsed = True
        template = "wagtail_daisIE/blocks/inputs/input.html"
        form_layout = blocks.BlockGroup(
            children=[
                "label",
                "input_type",
                "name",
                "placeholder",
                "value",
                "required",
                "helper_text",
                "error_text",
                "color",
                "size",
            ],
            settings=["design", "audience"],
        )


class TextareaBlock(ThemedBlock):
    label = blocks.CharBlock(max_length=255, label=_("Label"))
    name = blocks.CharBlock(
        max_length=64, required=False, blank=True, label=_("Field name")
    )
    placeholder = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Placeholder")
    )
    rows = blocks.IntegerBlock(min_value=2, max_value=20, default=3, label=_("Rows"))
    color = blocks.ChoiceBlock(
        choices=TEXTAREA_COLOR_CHOICES, required=False, label=_("Colour")
    )
    size = blocks.ChoiceBlock(
        choices=TEXTAREA_SIZE_CHOICES, required=False, label=_("Size")
    )
    required = blocks.BooleanBlock(default=False, required=False, label=_("Required"))
    helper_text = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Helper text")
    )
    error_text = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Error message")
    )

    class Meta:
        icon = "edit"
        group = _("Data input")
        collapsed = True
        template = "wagtail_daisIE/blocks/inputs/textarea.html"
        form_layout = blocks.BlockGroup(
            children=[
                "label",
                "name",
                "placeholder",
                "rows",
                "required",
                "helper_text",
                "error_text",
                "color",
                "size",
            ],
            settings=["design", "audience"],
        )


class SelectBlock(ThemedBlock):
    label = blocks.CharBlock(max_length=255, label=_("Label"))
    name = blocks.CharBlock(
        max_length=64, required=False, blank=True, label=_("Field name")
    )
    options = blocks.TextBlock(
        label=_("Options"),
        help_text=_("One option per line, or comma separated."),
    )
    placeholder = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Placeholder")
    )
    color = blocks.ChoiceBlock(
        choices=SELECT_COLOR_CHOICES, required=False, label=_("Colour")
    )
    size = blocks.ChoiceBlock(
        choices=SELECT_SIZE_CHOICES, required=False, label=_("Size")
    )
    helper_text = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Helper text")
    )
    error_text = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Error message")
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["select_options"] = _split_options((value or {}).get("options"))
        return context

    class Meta:
        icon = "list-ul"
        group = _("Data input")
        collapsed = True
        template = "wagtail_daisIE/blocks/inputs/select.html"
        form_layout = blocks.BlockGroup(
            children=[
                "label",
                "name",
                "options",
                "placeholder",
                "helper_text",
                "error_text",
                "color",
                "size",
            ],
            settings=["design", "audience"],
        )


class CheckboxBlock(ThemedBlock):
    label = blocks.CharBlock(max_length=255, label=_("Label"))
    name = blocks.CharBlock(
        max_length=64, required=False, blank=True, label=_("Field name")
    )
    checked = blocks.BooleanBlock(
        default=False, required=False, label=_("Checked by default")
    )
    color = blocks.ChoiceBlock(
        choices=CHOICE_COLOR_CHOICES, required=False, label=_("Colour")
    )
    size = blocks.ChoiceBlock(
        choices=CHOICE_SIZE_CHOICES, required=False, label=_("Size")
    )
    helper_text = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Helper text")
    )

    class Meta:
        icon = "tick-inverse"
        group = _("Data input")
        collapsed = True
        template = "wagtail_daisIE/blocks/inputs/checkbox.html"
        form_layout = blocks.BlockGroup(
            children=["label", "name", "checked", "helper_text", "color", "size"],
            settings=["design", "audience"],
        )


class ToggleBlock(ThemedBlock):
    label = blocks.CharBlock(max_length=255, label=_("Label"))
    name = blocks.CharBlock(
        max_length=64, required=False, blank=True, label=_("Field name")
    )
    checked = blocks.BooleanBlock(
        default=False, required=False, label=_("On by default")
    )
    color = blocks.ChoiceBlock(
        choices=TOGGLE_COLOR_CHOICES, required=False, label=_("Colour")
    )
    size = blocks.ChoiceBlock(
        choices=TOGGLE_SIZE_CHOICES, required=False, label=_("Size")
    )
    helper_text = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Helper text")
    )

    class Meta:
        icon = "cog"
        group = _("Data input")
        collapsed = True
        template = "wagtail_daisIE/blocks/inputs/toggle.html"
        form_layout = blocks.BlockGroup(
            children=["label", "name", "checked", "helper_text", "color", "size"],
            settings=["design", "audience"],
        )


class RadioBlock(ThemedBlock):
    label = blocks.CharBlock(max_length=255, label=_("Label"))
    name = blocks.CharBlock(
        max_length=64, required=False, blank=True, label=_("Group name")
    )
    options = blocks.TextBlock(
        label=_("Options"),
        help_text=_("One option per line, or comma separated."),
    )
    color = blocks.ChoiceBlock(
        choices=RADIO_COLOR_CHOICES, required=False, label=_("Colour")
    )
    size = blocks.ChoiceBlock(
        choices=RADIO_SIZE_CHOICES, required=False, label=_("Size")
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["radio_options"] = _split_options((value or {}).get("options"))
        return context

    class Meta:
        icon = "radio-empty"
        group = _("Data input")
        collapsed = True
        template = "wagtail_daisIE/blocks/inputs/radio.html"
        form_layout = blocks.BlockGroup(
            children=["label", "name", "options", "color", "size"],
            settings=["design", "audience"],
        )


class RangeBlock(ThemedBlock):
    label = blocks.CharBlock(max_length=255, label=_("Label"))
    name = blocks.CharBlock(
        max_length=64, required=False, blank=True, label=_("Field name")
    )
    minimum = blocks.IntegerBlock(default=0, label=_("Minimum"))
    maximum = blocks.IntegerBlock(default=100, label=_("Maximum"))
    step = blocks.IntegerBlock(min_value=1, default=1, label=_("Step"))
    value = blocks.IntegerBlock(default=40, label=_("Value"))
    color = blocks.ChoiceBlock(
        choices=RANGE_COLOR_CHOICES, required=False, label=_("Colour")
    )
    size = blocks.ChoiceBlock(
        choices=RANGE_SIZE_CHOICES, required=False, label=_("Size")
    )

    class Meta:
        icon = "horizontalrule"
        group = _("Data input")
        collapsed = True
        template = "wagtail_daisIE/blocks/inputs/range.html"
        form_layout = blocks.BlockGroup(
            children=[
                "label",
                "name",
                "minimum",
                "maximum",
                "step",
                "value",
                "color",
                "size",
            ],
            settings=["design", "audience"],
        )


class RatingBlock(ThemedBlock):
    label = blocks.CharBlock(max_length=255, required=False, label=_("Label"))
    name = blocks.CharBlock(
        max_length=64, required=False, blank=True, label=_("Group name")
    )
    maximum = blocks.IntegerBlock(
        min_value=1, max_value=10, default=5, label=_("Stars")
    )
    value = blocks.IntegerBlock(default=0, label=_("Selected"))
    size = blocks.ChoiceBlock(
        choices=RATING_SIZE_CHOICES, required=False, label=_("Size")
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
        maximum = int(value.get("maximum", 5) or 5)
        context["stars"] = range(1, maximum + 1)
        context["selected"] = int(value.get("value", 0) or 0)
        return context

    class Meta:
        icon = "star"
        group = _("Data input")
        collapsed = True
        template = "wagtail_daisIE/blocks/inputs/rating.html"
        form_layout = blocks.BlockGroup(
            children=["label", "name", "maximum", "value", "size"],
            settings=["design", "audience"],
        )


class FileInputBlock(ThemedBlock):
    label = blocks.CharBlock(max_length=255, label=_("Label"))
    name = blocks.CharBlock(
        max_length=64, required=False, blank=True, label=_("Field name")
    )
    accept = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Accepted types")
    )
    color = blocks.ChoiceBlock(
        choices=FILE_COLOR_CHOICES, required=False, label=_("Colour")
    )
    size = blocks.ChoiceBlock(
        choices=FILE_SIZE_CHOICES, required=False, label=_("Size")
    )
    helper_text = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Helper text")
    )

    class Meta:
        icon = "upload"
        group = _("Data input")
        collapsed = True
        template = "wagtail_daisIE/blocks/inputs/file.html"
        form_layout = blocks.BlockGroup(
            children=["label", "name", "accept", "helper_text", "color", "size"],
            settings=["design", "audience"],
        )


FIELD_BLOCKS = [
    ("input", InputBlock()),
    ("textarea", TextareaBlock()),
    ("select", SelectBlock()),
    ("checkbox", CheckboxBlock()),
    ("toggle", ToggleBlock()),
    ("radio", RadioBlock()),
    ("range", RangeBlock()),
    ("rating", RatingBlock()),
    ("file", FileInputBlock()),
]


class FieldsetBlock(ThemedBlock):
    legend = blocks.CharBlock(max_length=255, label=_("Legend"))
    description = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Description")
    )
    content = blocks.StreamBlock(FIELD_BLOCKS, label=_("Fields"))

    class Meta:
        icon = "folder-open-inverse"
        group = _("Data input")
        collapsed = True
        template = "wagtail_daisIE/blocks/inputs/fieldset.html"
        form_layout = blocks.BlockGroup(
            children=["legend", "description", "content"],
            settings=["design", "audience"],
        )


INPUT_BLOCKS = [*FIELD_BLOCKS, ("fieldset", FieldsetBlock())]
