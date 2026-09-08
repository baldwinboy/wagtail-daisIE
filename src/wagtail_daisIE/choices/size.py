from django.utils.translation import gettext_lazy as _

from .utils import make_auto_spacing_choices, make_choices


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


def make_inline_size_choices(prefix):
    return [
        *make_auto_spacing_choices(prefix),
        *make_choices(prefix, _SMALL_NUMERIC_SIZES, prepend_none=False),
        *make_choices(prefix, _SEMATIC_SIZES, prepend_none=False),
        *make_choices(prefix, _LARGE_NUMERIC_SIZES, prepend_none=False),
        *make_choices(prefix, _INLINE_RESPONSIVE_SIZES, prepend_none=False),
    ]


def make_block_size_choices(prefix):
    return [
        *make_auto_spacing_choices(prefix),
        *make_choices(prefix, _SMALL_NUMERIC_SIZES, prepend_none=False),
        *make_choices(prefix, _SEMATIC_SIZES, prepend_none=False),
        *make_choices(prefix, _LARGE_NUMERIC_SIZES, prepend_none=False),
        *make_choices(prefix, _BLOCK_RESPONSIVE_SIZES, prepend_none=False),
    ]


# Height choices

INLINE_MIN_HEIGHT_CHOICES = make_inline_size_choices("min-h-")
INLINE_HEIGHT_CHOICES = make_inline_size_choices("h-")
INLINE_MAX_HEIGHT_CHOICES = make_inline_size_choices("max-h-")

BLOCK_MIN_HEIGHT_CHOICES = make_block_size_choices("min-h-")
BLOCK_HEIGHT_CHOICES = make_block_size_choices("h-")
BLOCK_MAX_HEIGHT_CHOICES = make_block_size_choices("max-h-")

# Width choices

INLINE_MIN_WIDTH_CHOICES = make_inline_size_choices("min-w-")
INLINE_WIDTH_CHOICES = make_inline_size_choices("w-")
INLINE_MAX_WIDTH_CHOICES = make_inline_size_choices("max-w-")

BLOCK_MIN_WIDTH_CHOICES = make_block_size_choices("min-w-")
BLOCK_WIDTH_CHOICES = make_block_size_choices("w-")
BLOCK_MAX_WIDTH_CHOICES = make_block_size_choices("max-w-")

# Size choices (width + height)

INLINE_SIZE_CHOICES = make_inline_size_choices("size-")
BLOCK_SIZE_CHOICES = make_block_size_choices("size-")

# Aspect ratio text choices
ASPECT_RATIO_CHOICES = [
    ("square", "square"),
    ("video", "video"),
    ("auto", "auto"),
    ("<number>:<number>", "<number>:<number>, e.g. 16:9"),
]
