"""DaisyUI feedback component class choices."""

from .utils import ChoiceList


ALERT_COLOR_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("alert-info", "Info"),
        ("alert-success", "Success"),
        ("alert-warning", "Warning"),
        ("alert-error", "Error"),
    ],
    "ALERT_COLOR_CHOICES",
)

ALERT_STYLE_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("alert-outline", "Outline"),
        ("alert-dash", "Dash"),
        ("alert-soft", "Soft"),
    ],
    "ALERT_STYLE_CHOICES",
)

ALERT_DIRECTION_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("alert-vertical", "Vertical"),
        ("alert-horizontal", "Horizontal"),
    ],
    "ALERT_DIRECTION_CHOICES",
)

STATUS_COLOR_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("status-neutral", "Neutral"),
        ("status-primary", "Primary"),
        ("status-secondary", "Secondary"),
        ("status-accent", "Accent"),
        ("status-info", "Info"),
        ("status-success", "Success"),
        ("status-warning", "Warning"),
        ("status-error", "Error"),
    ],
    "STATUS_COLOR_CHOICES",
)

STATUS_SIZE_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("status-xs", "xs"),
        ("status-sm", "sm"),
        ("status-md", "md"),
        ("status-lg", "lg"),
        ("status-xl", "xl"),
    ],
    "STATUS_SIZE_CHOICES",
)

PROGRESS_COLOR_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("progress-neutral", "Neutral"),
        ("progress-primary", "Primary"),
        ("progress-secondary", "Secondary"),
        ("progress-accent", "Accent"),
        ("progress-info", "Info"),
        ("progress-success", "Success"),
        ("progress-warning", "Warning"),
        ("progress-error", "Error"),
    ],
    "PROGRESS_COLOR_CHOICES",
)

LOADING_STYLE_CHOICES = ChoiceList(
    [
        ("loading-spinner", "Spinner"),
        ("loading-dots", "Dots"),
        ("loading-ring", "Ring"),
        ("loading-ball", "Ball"),
        ("loading-bars", "Bars"),
        ("loading-infinity", "Infinity"),
    ],
    "LOADING_STYLE_CHOICES",
)

LOADING_SIZE_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("loading-xs", "xs"),
        ("loading-sm", "sm"),
        ("loading-md", "md"),
        ("loading-lg", "lg"),
        ("loading-xl", "xl"),
    ],
    "LOADING_SIZE_CHOICES",
)

TOAST_POSITION_CHOICES = ChoiceList(
    [
        ("toast-end toast-bottom", "Bottom end"),
        ("toast-start toast-bottom", "Bottom start"),
        ("toast-center toast-bottom", "Bottom centre"),
        ("toast-end toast-top", "Top end"),
        ("toast-start toast-top", "Top start"),
        ("toast-center toast-top", "Top centre"),
    ],
    "TOAST_POSITION_CHOICES",
)

TOOLTIP_POSITION_CHOICES = ChoiceList(
    [
        ("", "Top"),
        ("tooltip-top", "Top"),
        ("tooltip-bottom", "Bottom"),
        ("tooltip-left", "Left"),
        ("tooltip-right", "Right"),
    ],
    "TOOLTIP_POSITION_CHOICES",
)

TOOLTIP_COLOR_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("tooltip-primary", "Primary"),
        ("tooltip-secondary", "Secondary"),
        ("tooltip-accent", "Accent"),
        ("tooltip-info", "Info"),
        ("tooltip-success", "Success"),
        ("tooltip-warning", "Warning"),
        ("tooltip-error", "Error"),
    ],
    "TOOLTIP_COLOR_CHOICES",
)

STEPS_DIRECTION_CHOICES = ChoiceList(
    [
        ("steps-horizontal", "Horizontal"),
        ("steps-vertical", "Vertical"),
    ],
    "STEPS_DIRECTION_CHOICES",
)

STEPS_COLOR_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("step-neutral", "Neutral"),
        ("step-primary", "Primary"),
        ("step-secondary", "Secondary"),
        ("step-accent", "Accent"),
        ("step-info", "Info"),
        ("step-success", "Success"),
        ("step-warning", "Warning"),
        ("step-error", "Error"),
    ],
    "STEPS_COLOR_CHOICES",
)
