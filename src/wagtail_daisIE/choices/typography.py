from django.utils.translation import gettext_lazy as _

from .colors import DAISYUI_COLOR_TOKENS
from .utils import ChoiceList, make_choices


_SEMANTIC_FONT_SIZES = [
    ("xs", "xs"),
    ("sm", "sm"),
    ("md", "md"),
    ("lg", "lg"),
    ("xl", "xl"),
]
_NUMERIC_FONT_SIZES = [(f"{i}xl", (f"{i}xl")) for i in range(2, 41)]

FONT_SIZE_CHOICES = ChoiceList(
    [
        *make_choices("text-", _SEMANTIC_FONT_SIZES, will_inherit=True),
        *make_choices("text-", _NUMERIC_FONT_SIZES, prepend_none=False),
    ],
    "FONT_SIZE_CHOICES",
)

_FONT_WEIGHTS = [
    ("thin", _("Thin (100)")),
    ("extralight", _("Extra light (200)")),
    ("light", _("Light (300)")),
    ("normal", _("Normal (400)")),
    ("medium", _("Medium (500)")),
    ("semibold", _("Semibold (600)")),
    ("bold", _("Bold (700)")),
    ("extrabold", _("Extra bold (800)")),
    ("black", _("Black (900)")),
]

FONT_WEIGHT_CHOICES = ChoiceList(
    make_choices(
        "font-",
        _FONT_WEIGHTS,
        will_inherit=True,
    ),
    "FONT_WEIGHT_CHOICES",
)

_TEXT_ALIGNMENTS = [
    ("left", _("Left")),
    ("center", _("Center")),
    ("right", _("Right")),
    ("justify", _("Justify")),
]

TEXT_ALIGN_CHOICES = ChoiceList(
    make_choices(
        "text-",
        _TEXT_ALIGNMENTS,
        will_inherit=True,
    ),
    "TEXT_ALIGN_CHOICES",
)

_LINE_HEIGHTS = [
    ("none", "none (1)"),
    ("tight", "tight (1.25)"),
    ("snug", "snug (1.375)"),
    ("normal", "normal (1.5)"),
    ("relaxed", "relaxed (1.625)"),
    ("loose", "loose (2)"),
]

LINE_HEIGHT_CHOICES = ChoiceList(
    make_choices(
        "leading-",
        _LINE_HEIGHTS,
        will_inherit=True,
    ),
    "LINE_HEIGHT_CHOICES",
)

_LETTER_SPACING = [
    ("tighter", "tighter (-0.05em)"),
    ("tight", "tight (-0.025em)"),
    ("normal", "normal (0)"),
    ("wide", "wide (0.025em)"),
    ("wider", "wider (0.05em)"),
    ("widest", "widest (0.1em)"),
]

LETTER_SPACING_CHOICES = ChoiceList(
    make_choices(
        "tracking-",
        _LETTER_SPACING,
        will_inherit=True,
    ),
    "LETTER_SPACING_CHOICES",
)

TEXT_DECORATION_CHOICES = ChoiceList(
    [
        ("", _("None (inherit)")),
        ("no-underline", _("No underline")),
        ("underline", _("Underline")),
        ("overline", _("Overline")),
        ("line-through", _("Line through")),
    ],
    "TEXT_DECORATION_CHOICES",
)

DECORATION_COLOR_CHOICES = ChoiceList(
    make_choices(
        "decoration-",
        DAISYUI_COLOR_TOKENS,
        will_inherit=True,
    ),
    "DECORATION_COLOR_CHOICES",
)

_DECORATION_THICKNESS = [
    ("0", "0"),
    ("1", "1px"),
    ("2", "2px"),
    ("4", "4px"),
    ("8", "8px"),
    ("auto", _("Auto")),
    ("from-font", _("From font")),
]

DECORATION_THICKNESS_CHOICES = ChoiceList(
    make_choices(
        "decoration-",
        _DECORATION_THICKNESS,
        will_inherit=True,
    ),
    "DECORATION_THICKNESS_CHOICES",
)

FONT_FAMILY_ROLE_CHOICES = ChoiceList(
    [
        ("heading", "Heading"),
        ("subheading", "Subheading"),
        ("body", "Body"),
        ("code", "Code"),
        ("custom", "Custom"),
    ],
    "FONT_FAMILY_ROLE_CHOICES",
)

GENERIC_FONT_FAMILY_CHOICES = ChoiceList(
    [
        ("sans-serif", "Sans serif"),
        ("serif", "Serif"),
        ("monospace", "Monospace"),
        ("cursive", "Cursive"),
        ("fantasy", "Fantasy"),
        ("system-ui", "System UI"),
        ("ui-sans-serif", "UI sans-serif"),
        ("ui-serif", "UI serif"),
        ("ui-monospace", "UI monospace"),
        ("emoji", "Emoji"),
        ("math", "Math"),
        ("fangsong", "Fangsong"),
    ],
    "GENERIC_FONT_FAMILY_CHOICES",
)
