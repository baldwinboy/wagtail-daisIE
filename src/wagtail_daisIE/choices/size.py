from django.utils.translation import gettext_lazy as _

from .utils import (
    ChoiceList,
    make_auto_spacing_choices,
    make_choices,
    make_spacing_choices,
)


_SMALL_NUMERIC_SIZES = [(f"{i}xs", (f"{i}xs")) for i in range(2, 4)]

_SEMATIC_SIZES = [
    ("xs", "xs"),
    ("sm", "sm"),
    ("md", "md"),
    ("lg", "lg"),
    ("xl", "xl"),
]

_LARGE_NUMERIC_SIZES = [(f"{i}xl", (f"{i}xl")) for i in range(2, 8)]

_INLINE_RESPONSIVE_SIZES = [
    ("full", _("Full")),
    ("min", _("Min")),
    ("max", _("Max")),
    ("fit", _("Fit")),
    ("svw", _("Smallest visible width")),
    ("svh", _("Smallest visible height")),
]

_BLOCK_RESPONSIVE_SIZES = [
    *_INLINE_RESPONSIVE_SIZES,
    ("screen", _("Screen")),
    ("dvw", _("Device width")),
    ("dvh", _("Device height")),
    ("lvw", _("Largest visible width")),
    ("lvh", _("Largest visible height")),
]

# Max-height supports the numeric spacing scale plus a small set of intrinsic
# values. The old semantic values are retained below for stored content.
_MAX_HEIGHT_RESPONSIVE_SIZES = [
    ("full", _("Full")),
    ("min", _("Min")),
    ("max", _("Max")),
    ("fit", _("Fit")),
    ("screen", _("Screen")),
    ("svh", _("Smallest visible height")),
    ("lvh", _("Largest visible height")),
    ("dvh", _("Device height")),
]


def _make_size_choices(prefix, responsive_sizes, include_auto):
    auto_choices = (
        make_auto_spacing_choices(prefix) if include_auto else [("", _("None"))]
    )
    return [
        *auto_choices,
        *make_choices(prefix, _SMALL_NUMERIC_SIZES, prepend_none=False),
        *make_choices(prefix, _SEMATIC_SIZES, prepend_none=False),
        *make_choices(prefix, _LARGE_NUMERIC_SIZES, prepend_none=False),
        *make_choices(prefix, responsive_sizes, prepend_none=False),
    ]


def make_inline_size_choices(prefix, include_auto=True):
    return _make_size_choices(prefix, _INLINE_RESPONSIVE_SIZES, include_auto)


def make_block_size_choices(prefix, include_auto=True):
    return _make_size_choices(prefix, _BLOCK_RESPONSIVE_SIZES, include_auto)


def make_max_height_choices():
    """Return valid Tailwind max-height choices plus legacy saved values."""
    return [
        ("", _("None")),
        *make_spacing_choices("max-h-", prepend_none=False),
        *make_choices("max-h-", _MAX_HEIGHT_RESPONSIVE_SIZES, prepend_none=False),
        # Keep the pre-existing semantic values valid for stored content.
        *make_choices("max-h-", _SMALL_NUMERIC_SIZES, prepend_none=False),
        *make_choices("max-h-", _SEMATIC_SIZES, prepend_none=False),
        *make_choices("max-h-", _LARGE_NUMERIC_SIZES, prepend_none=False),
    ]


# Height choices

INLINE_MIN_HEIGHT_CHOICES = ChoiceList(
    make_inline_size_choices("min-h-"), "INLINE_MIN_HEIGHT_CHOICES"
)
INLINE_HEIGHT_CHOICES = ChoiceList(
    make_inline_size_choices("h-"), "INLINE_HEIGHT_CHOICES"
)
INLINE_MAX_HEIGHT_CHOICES = ChoiceList(
    make_max_height_choices(),
    "INLINE_MAX_HEIGHT_CHOICES",
)

BLOCK_MIN_HEIGHT_CHOICES = ChoiceList(
    make_block_size_choices("min-h-"), "BLOCK_MIN_HEIGHT_CHOICES"
)
BLOCK_HEIGHT_CHOICES = ChoiceList(make_block_size_choices("h-"), "BLOCK_HEIGHT_CHOICES")
BLOCK_MAX_HEIGHT_CHOICES = ChoiceList(
    make_max_height_choices(),
    "BLOCK_MAX_HEIGHT_CHOICES",
)

# Width choices

INLINE_MIN_WIDTH_CHOICES = ChoiceList(
    make_inline_size_choices("min-w-"), "INLINE_MIN_WIDTH_CHOICES"
)
INLINE_WIDTH_CHOICES = ChoiceList(
    make_inline_size_choices("w-"), "INLINE_WIDTH_CHOICES"
)
INLINE_MAX_WIDTH_CHOICES = ChoiceList(
    make_inline_size_choices("max-w-", include_auto=False),
    "INLINE_MAX_WIDTH_CHOICES",
)

BLOCK_MIN_WIDTH_CHOICES = ChoiceList(
    make_block_size_choices("min-w-"), "BLOCK_MIN_WIDTH_CHOICES"
)
BLOCK_WIDTH_CHOICES = ChoiceList(make_block_size_choices("w-"), "BLOCK_WIDTH_CHOICES")
BLOCK_MAX_WIDTH_CHOICES = ChoiceList(
    make_block_size_choices("max-w-", include_auto=False),
    "BLOCK_MAX_WIDTH_CHOICES",
)

# Size choices (width + height)

INLINE_SIZE_CHOICES = ChoiceList(
    make_inline_size_choices("size-"), "INLINE_SIZE_CHOICES"
)
BLOCK_SIZE_CHOICES = ChoiceList(make_block_size_choices("size-"), "BLOCK_SIZE_CHOICES")

# Aspect ratio text choices
ASPECT_RATIO_CHOICES = ChoiceList(
    [
        ("square", "square"),
        ("video", "video"),
        ("auto", "auto"),
        ("<number>:<number>", "<number>:<number>, e.g. 16:9"),
    ],
    "ASPECT_RATIO_CHOICES",
)
