"""DaisyUI feedback component blocks.

These let editors compose alerts, toasts, progress, loading indicators and
dialogs without writing markup. They are regular content blocks, so they can be
placed anywhere in a page body.
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks import ThemedBlock
from ..choices.feedback import (
    ALERT_COLOR_CHOICES,
    ALERT_DIRECTION_CHOICES,
    ALERT_STYLE_CHOICES,
    LOADING_SIZE_CHOICES,
    LOADING_STYLE_CHOICES,
    PROGRESS_COLOR_CHOICES,
    STATUS_COLOR_CHOICES,
    STATUS_SIZE_CHOICES,
    STEPS_COLOR_CHOICES,
    STEPS_DIRECTION_CHOICES,
    TOAST_POSITION_CHOICES,
    TOOLTIP_COLOR_CHOICES,
    TOOLTIP_POSITION_CHOICES,
)
from ..icons.blocks import IconChooserBlock


class AlertBlock(ThemedBlock):
    content = blocks.RichTextBlock(label=_("Message"))
    icon = IconChooserBlock(required=False)
    color = blocks.ChoiceBlock(
        choices=ALERT_COLOR_CHOICES, required=False, label=_("Colour")
    )
    style = blocks.ChoiceBlock(
        choices=ALERT_STYLE_CHOICES, required=False, label=_("Style")
    )
    direction = blocks.ChoiceBlock(
        choices=ALERT_DIRECTION_CHOICES, required=False, label=_("Direction")
    )

    class Meta:
        icon = "warning"
        group = _("Feedback")
        collapsed = True
        template = "wagtail_daisIE/blocks/feedback/alert.html"
        form_layout = blocks.BlockGroup(
            children=["content", "icon", "color", "style", "direction"],
            settings=["design", "audience"],
        )


class StatusBlock(ThemedBlock):
    color = blocks.ChoiceBlock(
        choices=STATUS_COLOR_CHOICES, required=False, label=_("Colour")
    )
    size = blocks.ChoiceBlock(
        choices=STATUS_SIZE_CHOICES, required=False, label=_("Size")
    )
    label = blocks.CharBlock(
        max_length=128,
        required=False,
        label=_("Label"),
        help_text=_("Optional text shown next to the indicator."),
    )

    class Meta:
        icon = "circle"
        group = _("Feedback")
        collapsed = True
        template = "wagtail_daisIE/blocks/feedback/status.html"
        form_layout = blocks.BlockGroup(
            children=["label", "color", "size"],
            settings=["design", "audience"],
        )


class ProgressBlock(ThemedBlock):
    value = blocks.IntegerBlock(
        min_value=0, max_value=100, default=50, label=_("Value (%)")
    )
    maximum = blocks.IntegerBlock(min_value=1, default=100, label=_("Maximum"))
    color = blocks.ChoiceBlock(
        choices=PROGRESS_COLOR_CHOICES, required=False, label=_("Colour")
    )
    label = blocks.CharBlock(
        max_length=128, required=False, label=_("Accessible label")
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
        maximum = int(value.get("maximum", 100) or 100)
        context["progress_value"] = min(int(value.get("value", 0) or 0), maximum)
        return context

    class Meta:
        icon = "tasks"
        group = _("Feedback")
        collapsed = True
        template = "wagtail_daisIE/blocks/feedback/progress.html"
        form_layout = blocks.BlockGroup(
            children=["value", "maximum", "color", "label"],
            settings=["design", "audience"],
        )


class RadialProgressBlock(ThemedBlock):
    value = blocks.IntegerBlock(
        min_value=0, max_value=100, default=70, label=_("Value (%)")
    )
    size = blocks.IntegerBlock(
        min_value=1, max_value=20, default=5, label=_("Size (rem)")
    )
    thickness = blocks.CharBlock(
        default="0.25rem", required=False, label=_("Thickness")
    )

    class Meta:
        icon = "circle"
        group = _("Feedback")
        collapsed = True
        template = "wagtail_daisIE/blocks/feedback/radial_progress.html"
        form_layout = blocks.BlockGroup(
            children=["value", "size", "thickness"],
            settings=["design", "audience"],
        )


class LoadingBlock(ThemedBlock):
    style = blocks.ChoiceBlock(
        choices=LOADING_STYLE_CHOICES, default="loading-spinner", label=_("Style")
    )
    size = blocks.ChoiceBlock(
        choices=LOADING_SIZE_CHOICES, required=False, label=_("Size")
    )
    label = blocks.CharBlock(
        max_length=128,
        default="Loading",
        label=_("Screen reader label"),
    )

    class Meta:
        icon = "spinner"
        group = _("Feedback")
        collapsed = True
        template = "wagtail_daisIE/blocks/feedback/loading.html"
        form_layout = blocks.BlockGroup(
            children=["style", "size", "label"],
            settings=["design", "audience"],
        )


class ToastBlock(ThemedBlock):
    position = blocks.ChoiceBlock(
        choices=TOAST_POSITION_CHOICES,
        default="toast-end toast-bottom",
        label=_("Position"),
    )
    color = blocks.ChoiceBlock(
        choices=ALERT_COLOR_CHOICES, default="alert-info", label=_("Colour")
    )
    content = blocks.RichTextBlock(label=_("Message"))

    class Meta:
        icon = "download"
        group = _("Feedback")
        collapsed = True
        template = "wagtail_daisIE/blocks/feedback/toast.html"
        form_layout = blocks.BlockGroup(
            children=["content", "color", "position"],
            settings=["design", "audience"],
        )


class ModalBlock(ThemedBlock):
    trigger_label = blocks.CharBlock(
        max_length=64, default="Open", label=_("Trigger label")
    )
    title = blocks.CharBlock(max_length=255, required=False, label=_("Title"))
    content = blocks.RichTextBlock(required=False, label=_("Content"))
    close_label = blocks.CharBlock(
        max_length=64, default="Close", required=False, label=_("Close label")
    )
    placement = blocks.ChoiceBlock(
        choices=[
            ("", "Centre"),
            ("modal-top", "Top"),
            ("modal-middle", "Middle"),
            ("modal-bottom", "Bottom"),
            ("modal-start", "Start"),
            ("modal-end", "End"),
        ],
        default="",
        required=False,
        label=_("Placement"),
    )

    class Meta:
        icon = "dialog"
        group = _("Feedback")
        collapsed = True
        template = "wagtail_daisIE/blocks/feedback/modal.html"
        form_layout = blocks.BlockGroup(
            children=["trigger_label", "title", "content", "close_label", "placement"],
            settings=["design", "audience"],
        )


class TooltipBlock(ThemedBlock):
    text = blocks.CharBlock(max_length=255, label=_("Tooltip text"))
    content = blocks.CharBlock(max_length=255, label=_("Trigger text"))
    position = blocks.ChoiceBlock(
        choices=TOOLTIP_POSITION_CHOICES, required=False, label=_("Position")
    )
    color = blocks.ChoiceBlock(
        choices=TOOLTIP_COLOR_CHOICES, required=False, label=_("Colour")
    )

    class Meta:
        icon = "info"
        group = _("Feedback")
        collapsed = True
        template = "wagtail_daisIE/blocks/feedback/tooltip.html"
        form_layout = blocks.BlockGroup(
            children=["content", "text", "position", "color"],
            settings=["design", "audience"],
        )


class StepsBlock(ThemedBlock):
    direction = blocks.ChoiceBlock(
        choices=STEPS_DIRECTION_CHOICES,
        default="steps-horizontal",
        label=_("Direction"),
    )
    color = blocks.ChoiceBlock(
        choices=STEPS_COLOR_CHOICES, required=False, label=_("Colour")
    )
    active = blocks.IntegerBlock(min_value=0, default=1, label=_("Completed steps"))
    steps = blocks.ListBlock(blocks.CharBlock(label=_("Step")), label=_("Steps"))

    class Meta:
        icon = "list-ul"
        group = _("Feedback")
        collapsed = True
        template = "wagtail_daisIE/blocks/feedback/steps.html"
        form_layout = blocks.BlockGroup(
            children=["steps", "active", "direction", "color"],
            settings=["design", "audience"],
        )


FEEDBACK_BLOCKS = [
    ("alert", AlertBlock()),
    ("status", StatusBlock()),
    ("progress", ProgressBlock()),
    ("radial_progress", RadialProgressBlock()),
    ("loading", LoadingBlock()),
    ("toast", ToastBlock()),
    ("modal", ModalBlock()),
    ("tooltip", TooltipBlock()),
    ("steps", StepsBlock()),
]
