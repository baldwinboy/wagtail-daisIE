from django.utils.translation import gettext_lazy as _

from .utils import kebab_to_sentence, make_choices


DAISYUI_COLOR_TOKENS = [
    "primary",
    "primary-content",
    "secondary",
    "secondary-content",
    "accent",
    "accent-content",
    "neutral",
    "neutral-content",
    "base-100",
    "base-200",
    "base-300",
    "base-content",
    "info",
    "info-content",
    "success",
    "success-content",
    "warning",
    "warning-content",
    "error",
    "error-content",
]

DAISYUI_COLOR_TOKENS = [
    (f"{token}", _(kebab_to_sentence(token))) for token in DAISYUI_COLOR_TOKENS
]

DAISYUI_BG_COLOR_CHOICES = make_choices(
    "bg-",
    DAISYUI_COLOR_TOKENS,
    will_inherit=True,
)


DAISYUI_TEXT_COLOR_CHOICES = make_choices(
    "text-",
    DAISYUI_COLOR_TOKENS,
    will_inherit=True,
)

DAISYUI_BORDER_COLOR_CHOICES = make_choices(
    "border-",
    DAISYUI_COLOR_TOKENS,
    will_inherit=True,
)
