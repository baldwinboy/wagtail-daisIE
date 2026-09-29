"""DaisyUI data-input component class choices."""

from .utils import ChoiceList


INPUT_TYPE_CHOICES = ChoiceList(
    [
        ("text", "Text"),
        ("email", "Email"),
        ("url", "URL"),
        ("password", "Password"),
        ("number", "Number"),
        ("search", "Search"),
        ("tel", "Telephone"),
        ("date", "Date"),
        ("time", "Time"),
        ("datetime-local", "Date and time"),
    ],
    "INPUT_TYPE_CHOICES",
)

INPUT_COLOR_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("input-neutral", "Neutral"),
        ("input-primary", "Primary"),
        ("input-secondary", "Secondary"),
        ("input-accent", "Accent"),
        ("input-info", "Info"),
        ("input-success", "Success"),
        ("input-warning", "Warning"),
        ("input-error", "Error"),
    ],
    "INPUT_COLOR_CHOICES",
)

INPUT_SIZE_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("input-xs", "xs"),
        ("input-sm", "sm"),
        ("input-md", "md"),
        ("input-lg", "lg"),
        ("input-xl", "xl"),
    ],
    "INPUT_SIZE_CHOICES",
)

TEXTAREA_COLOR_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("textarea-neutral", "Neutral"),
        ("textarea-primary", "Primary"),
        ("textarea-secondary", "Secondary"),
        ("textarea-accent", "Accent"),
        ("textarea-info", "Info"),
        ("textarea-success", "Success"),
        ("textarea-warning", "Warning"),
        ("textarea-error", "Error"),
    ],
    "TEXTAREA_COLOR_CHOICES",
)

TEXTAREA_SIZE_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("textarea-xs", "xs"),
        ("textarea-sm", "sm"),
        ("textarea-md", "md"),
        ("textarea-lg", "lg"),
        ("textarea-xl", "xl"),
    ],
    "TEXTAREA_SIZE_CHOICES",
)

SELECT_COLOR_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("select-neutral", "Neutral"),
        ("select-primary", "Primary"),
        ("select-secondary", "Secondary"),
        ("select-accent", "Accent"),
        ("select-info", "Info"),
        ("select-success", "Success"),
        ("select-warning", "Warning"),
        ("select-error", "Error"),
    ],
    "SELECT_COLOR_CHOICES",
)

SELECT_SIZE_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("select-xs", "xs"),
        ("select-sm", "sm"),
        ("select-md", "md"),
        ("select-lg", "lg"),
        ("select-xl", "xl"),
    ],
    "SELECT_SIZE_CHOICES",
)

CHOICE_COLOR_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("checkbox-neutral", "Neutral"),
        ("checkbox-primary", "Primary"),
        ("checkbox-secondary", "Secondary"),
        ("checkbox-accent", "Accent"),
        ("checkbox-info", "Info"),
        ("checkbox-success", "Success"),
        ("checkbox-warning", "Warning"),
        ("checkbox-error", "Error"),
    ],
    "CHOICE_COLOR_CHOICES",
)

CHOICE_SIZE_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("checkbox-xs", "xs"),
        ("checkbox-sm", "sm"),
        ("checkbox-md", "md"),
        ("checkbox-lg", "lg"),
        ("checkbox-xl", "xl"),
    ],
    "CHOICE_SIZE_CHOICES",
)

TOGGLE_COLOR_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("toggle-neutral", "Neutral"),
        ("toggle-primary", "Primary"),
        ("toggle-secondary", "Secondary"),
        ("toggle-accent", "Accent"),
        ("toggle-info", "Info"),
        ("toggle-success", "Success"),
        ("toggle-warning", "Warning"),
        ("toggle-error", "Error"),
    ],
    "TOGGLE_COLOR_CHOICES",
)

TOGGLE_SIZE_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("toggle-xs", "xs"),
        ("toggle-sm", "sm"),
        ("toggle-md", "md"),
        ("toggle-lg", "lg"),
        ("toggle-xl", "xl"),
    ],
    "TOGGLE_SIZE_CHOICES",
)

RADIO_SIZE_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("radio-xs", "xs"),
        ("radio-sm", "sm"),
        ("radio-md", "md"),
        ("radio-lg", "lg"),
        ("radio-xl", "xl"),
    ],
    "RADIO_SIZE_CHOICES",
)

RANGE_SIZE_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("range-xs", "xs"),
        ("range-sm", "sm"),
        ("range-md", "md"),
        ("range-lg", "lg"),
        ("range-xl", "xl"),
    ],
    "RANGE_SIZE_CHOICES",
)

RADIO_COLOR_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("radio-neutral", "Neutral"),
        ("radio-primary", "Primary"),
        ("radio-secondary", "Secondary"),
        ("radio-accent", "Accent"),
        ("radio-info", "Info"),
        ("radio-success", "Success"),
        ("radio-warning", "Warning"),
        ("radio-error", "Error"),
    ],
    "RADIO_COLOR_CHOICES",
)

RANGE_COLOR_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("range-neutral", "Neutral"),
        ("range-primary", "Primary"),
        ("range-secondary", "Secondary"),
        ("range-accent", "Accent"),
        ("range-info", "Info"),
        ("range-success", "Success"),
        ("range-warning", "Warning"),
        ("range-error", "Error"),
    ],
    "RANGE_COLOR_CHOICES",
)

RATING_SIZE_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("rating-xs", "xs"),
        ("rating-sm", "sm"),
        ("rating-md", "md"),
        ("rating-lg", "lg"),
        ("rating-xl", "xl"),
    ],
    "RATING_SIZE_CHOICES",
)

FILE_COLOR_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("file-input-neutral", "Neutral"),
        ("file-input-primary", "Primary"),
        ("file-input-secondary", "Secondary"),
        ("file-input-accent", "Accent"),
        ("file-input-info", "Info"),
        ("file-input-success", "Success"),
        ("file-input-warning", "Warning"),
        ("file-input-error", "Error"),
    ],
    "FILE_COLOR_CHOICES",
)

FILE_SIZE_CHOICES = ChoiceList(
    [
        ("", "Default"),
        ("file-input-xs", "xs"),
        ("file-input-sm", "sm"),
        ("file-input-md", "md"),
        ("file-input-lg", "lg"),
        ("file-input-xl", "xl"),
    ],
    "FILE_SIZE_CHOICES",
)
