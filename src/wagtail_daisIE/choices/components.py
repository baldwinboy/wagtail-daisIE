"""Variant choices for the daisyUI component blocks."""

from django.utils.translation import gettext_lazy as _

from .colors import DAISYUI_COLOR_TOKENS
from .utils import ChoiceList, make_choices


# Badge
BADGE_COLOR_CHOICES = ChoiceList(
    make_choices("badge-", DAISYUI_COLOR_TOKENS, will_inherit=True),
    "BADGE_COLOR_CHOICES",
)
BADGE_STYLE_CHOICES = ChoiceList(
    make_choices(
        "badge-",
        [
            ("outline", _("Outline")),
            ("dash", _("Dashed")),
            ("soft", _("Soft")),
            ("ghost", _("Ghost")),
        ],
        will_inherit=True,
    ),
    "BADGE_STYLE_CHOICES",
)
BADGE_SIZE_CHOICES = ChoiceList(
    make_choices(
        "badge-",
        [("xs", "xs"), ("sm", "sm"), ("md", "md"), ("lg", "lg"), ("xl", "xl")],
        will_inherit=True,
    ),
    "BADGE_SIZE_CHOICES",
)

# Divider
DIVIDER_COLOR_CHOICES = ChoiceList(
    make_choices("divider-", DAISYUI_COLOR_TOKENS, will_inherit=True),
    "DIVIDER_COLOR_CHOICES",
)
DIVIDER_POSITION_CHOICES = ChoiceList(
    [
        ("", _("Center")),
        ("divider-start", _("Start")),
        ("divider-end", _("End")),
    ],
    "DIVIDER_POSITION_CHOICES",
)
DIVIDER_ORIENTATION_CHOICES = ChoiceList(
    [
        ("", _("Horizontal")),
        ("divider-horizontal", _("Horizontal (with content)")),
        ("divider-vertical", _("Vertical")),
    ],
    "DIVIDER_ORIENTATION_CHOICES",
)

# Avatar
AVATAR_SIZE_CHOICES = ChoiceList(
    make_choices(
        "",
        [
            ("w-8", "xs"),
            ("w-10", "sm"),
            ("w-12", "md"),
            ("w-16", "lg"),
            ("w-20", "xl"),
            ("w-24", "2xl"),
            ("w-32", "3xl"),
        ],
        will_inherit=True,
    ),
    "AVATAR_SIZE_CHOICES",
)
AVATAR_SHAPE_CHOICES = ChoiceList(
    [
        ("", _("Square")),
        ("rounded", _("Rounded")),
        ("rounded-box", _("Rounded box")),
        ("rounded-full", _("Circle")),
    ],
    "AVATAR_SHAPE_CHOICES",
)
AVATAR_STATUS_CHOICES = ChoiceList(
    [
        ("", _("None")),
        ("avatar-online", _("Online")),
        ("avatar-offline", _("Offline")),
        ("avatar-placeholder", _("Placeholder")),
    ],
    "AVATAR_STATUS_CHOICES",
)

# Stat
STAT_COLOR_CHOICES = ChoiceList(
    make_choices("text-", DAISYUI_COLOR_TOKENS, will_inherit=True),
    "STAT_COLOR_CHOICES",
)

# Skeleton
SKELETON_SHAPE_CHOICES = ChoiceList(
    [
        ("skeleton", _("Block")),
        ("skeleton-text", _("Text")),
    ],
    "SKELETON_SHAPE_CHOICES",
)

# Layout / decorative
MASK_SHAPE_CHOICES = ChoiceList(
    [
        ("mask-squircle", _("Squircle")),
        ("mask-heart", _("Heart")),
        ("mask-hexagon", _("Hexagon")),
        ("mask-hexagon-2", _("Hexagon (flat)")),
        ("mask-decagon", _("Decagon")),
        ("mask-pentagon", _("Pentagon")),
        ("mask-diamond", _("Diamond")),
        ("mask-square", _("Square")),
        ("mask-circle", _("Circle")),
        ("mask-star", _("Star")),
        ("mask-star-2", _("Star (sharp)")),
        ("mask-triangle", _("Triangle")),
        ("mask-triangle-2", _("Triangle (down)")),
        ("mask-triangle-3", _("Triangle (left)")),
        ("mask-triangle-4", _("Triangle (right)")),
    ],
    "MASK_SHAPE_CHOICES",
)
DROPDOWN_POSITION_CHOICES = ChoiceList(
    [
        ("", _("Default")),
        ("dropdown-end", _("End")),
        ("dropdown-top", _("Top")),
        ("dropdown-bottom", _("Bottom")),
        ("dropdown-left", _("Left")),
        ("dropdown-right", _("Right")),
        ("dropdown-center", _("Center")),
        ("dropdown-hover", _("Open on hover")),
        ("dropdown-open", _("Open by default")),
    ],
    "DROPDOWN_POSITION_CHOICES",
)
SWAP_EFFECT_CHOICES = ChoiceList(
    [
        ("", _("None")),
        ("swap-rotate", _("Rotate")),
        ("swap-flip", _("Flip")),
    ],
    "SWAP_EFFECT_CHOICES",
)
INDICATOR_POSITION_CHOICES = ChoiceList(
    [
        ("indicator-top indicator-start", _("Top start")),
        ("indicator-top indicator-center", _("Top center")),
        ("indicator-top indicator-end", _("Top end")),
        ("indicator-middle indicator-start", _("Middle start")),
        ("indicator-middle indicator-center", _("Middle center")),
        ("indicator-middle indicator-end", _("Middle end")),
        ("indicator-bottom indicator-start", _("Bottom start")),
        ("indicator-bottom indicator-center", _("Bottom center")),
        ("indicator-bottom indicator-end", _("Bottom end")),
    ],
    "INDICATOR_POSITION_CHOICES",
)
INDICATOR_COLOR_CHOICES = ChoiceList(
    make_choices(
        "badge-",
        DAISYUI_COLOR_TOKENS,
        will_inherit=True,
    ),
    "INDICATOR_COLOR_CHOICES",
)

# Tabs
TABS_STYLE_CHOICES = ChoiceList(
    [
        ("tabs-box", _("Box")),
        ("tabs-border", _("Border")),
        ("tabs-lift", _("Lift")),
    ],
    "TABS_STYLE_CHOICES",
)
TABS_SIZE_CHOICES = ChoiceList(
    make_choices(
        "tabs-",
        [("xs", "xs"), ("sm", "sm"), ("md", "md"), ("lg", "lg"), ("xl", "xl")],
        will_inherit=True,
    ),
    "TABS_SIZE_CHOICES",
)
TABS_PLACEMENT_CHOICES = ChoiceList(
    [
        ("", _("Top")),
        ("tabs-bottom", _("Bottom")),
    ],
    "TABS_PLACEMENT_CHOICES",
)

# Carousel
CAROUSEL_ORIENTATION_CHOICES = ChoiceList(
    [
        ("", _("Horizontal")),
        ("carousel-vertical", _("Vertical")),
        ("carousel-center", _("Center")),
        ("carousel-end", _("End")),
    ],
    "CAROUSEL_ORIENTATION_CHOICES",
)

# OTP
OTP_SIZE_CHOICES = ChoiceList(
    make_choices(
        "otp-",
        [("xs", "xs"), ("sm", "sm"), ("md", "md"), ("lg", "lg"), ("xl", "xl")],
        will_inherit=True,
    ),
    "OTP_SIZE_CHOICES",
)
OTP_COLOR_CHOICES = ChoiceList(
    make_choices("otp-", DAISYUI_COLOR_TOKENS, will_inherit=True),
    "OTP_COLOR_CHOICES",
)

# Countdown
COUNTDOWN_SIZE_CHOICES = ChoiceList(
    make_choices(
        "text-",
        [("2xl", "2xl"), ("4xl", "4xl"), ("6xl", "6xl"), ("8xl", "8xl")],
        will_inherit=True,
    ),
    "COUNTDOWN_SIZE_CHOICES",
)

# Main container layout
MAIN_LAYOUT_CHOICES = ChoiceList(
    [
        ("column", _("Column")),
        ("row", _("Row")),
        ("grid", _("Grid")),
    ],
    "MAIN_LAYOUT_CHOICES",
)
MAIN_LAYOUT_CLASSES = {
    "column": "flex flex-col grow",
    "row": "flex flex-row grow",
    "grid": "grid grow",
}
MAIN_LAYOUT_CLASS_TOKENS = [
    token for value in MAIN_LAYOUT_CLASSES.values() for token in value.split()
]


__all__ = [
    "AVATAR_SHAPE_CHOICES",
    "AVATAR_SIZE_CHOICES",
    "AVATAR_STATUS_CHOICES",
    "BADGE_COLOR_CHOICES",
    "BADGE_SIZE_CHOICES",
    "BADGE_STYLE_CHOICES",
    "CAROUSEL_ORIENTATION_CHOICES",
    "COUNTDOWN_SIZE_CHOICES",
    "DIVIDER_COLOR_CHOICES",
    "DIVIDER_ORIENTATION_CHOICES",
    "DIVIDER_POSITION_CHOICES",
    "DROPDOWN_POSITION_CHOICES",
    "INDICATOR_COLOR_CHOICES",
    "INDICATOR_POSITION_CHOICES",
    "MAIN_LAYOUT_CHOICES",
    "MAIN_LAYOUT_CLASSES",
    "MAIN_LAYOUT_CLASS_TOKENS",
    "MASK_SHAPE_CHOICES",
    "OTP_COLOR_CHOICES",
    "OTP_SIZE_CHOICES",
    "SKELETON_SHAPE_CHOICES",
    "STAT_COLOR_CHOICES",
    "SWAP_EFFECT_CHOICES",
    "TABS_PLACEMENT_CHOICES",
    "TABS_SIZE_CHOICES",
    "TABS_STYLE_CHOICES",
]
