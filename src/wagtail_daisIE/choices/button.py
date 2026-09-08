from django.utils.translation import gettext_lazy as _

from wagtail_daisIE.choices.utils import make_choices


DAISYUI_BUTTON_COLORS = [
    ("neutral", _("Neutral")),
    ("primary", _("Primary")),
    ("secondary", _("Secondary")),
    ("accent", _("Accent")),
    ("info", _("Info")),
    ("success", _("Success")),
    ("warning", _("Warning")),
    ("error", _("Error")),
]

DAISYUI_BUTTON_COLOR_CHOICES = make_choices(
    "btn-",
    DAISYUI_BUTTON_COLORS,
    will_inherit=True,
)

DAISYUI_BUTTON_STYLES = [
    ("outline", _("Outline")),
    ("dash", _("Dashed")),
    ("soft", _("Soft")),
    ("ghost", _("Ghost")),
    ("link", _("Link style")),
]

DAISYUI_BUTTON_STYLE_CHOICES = make_choices(
    "btn-",
    DAISYUI_BUTTON_STYLES,
    will_inherit=True,
)

DAISYUI_BUTTON_SIZES = [
    ("xs", _("xs")),
    ("sm", _("sm")),
    ("md", _("md")),
    ("lg", _("lg")),
    ("xl", _("xl")),
]

DAISYUI_BUTTON_SIZE_CHOICES = make_choices(
    "btn-",
    DAISYUI_BUTTON_SIZES,
    will_inherit=True,
)

DAISYUI_BUTTON_BEHAVIORS = [
    ("active", _("Active")),
    ("disabled", _("Disabled")),
]

DAISYUI_BUTTON_BEHAVIOR_CHOICES = make_choices(
    "btn-",
    DAISYUI_BUTTON_BEHAVIORS,
    will_inherit=True,
)

DAISYUI_BUTTON_MODIFIERS = [
    ("wide", _("Wide")),
    ("block", _("Block")),
    ("square", _("Square")),
    ("circle", _("Circle")),
]

DAISYUI_BUTTON_MODIFIER_CHOICES = make_choices(
    "btn-",
    DAISYUI_BUTTON_MODIFIERS,
    will_inherit=True,
)
