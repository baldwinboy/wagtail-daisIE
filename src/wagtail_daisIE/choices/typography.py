from django.utils.translation import gettext_lazy as _

from .utils import make_choices


_SEMANTIC_FONT_SIZES = [
    ("xs", "xs"),
    ("sm", "sm"),
    ("md", "md"),
    ("lg", "lg"),
    ("xl", "xl"),
]
_NUMERIC_FONT_SIZES = [(f"{i}xl", (f"{i}xl")) for i in range(2, 41)]

FONT_SIZE_CHOICES = [
    *make_choices("text-", _SEMANTIC_FONT_SIZES, will_inherit=True),
    *make_choices("text-", _NUMERIC_FONT_SIZES, prepend_none=False),
]

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

FONT_WEIGHT_CHOICES = make_choices(
    "font-",
    _FONT_WEIGHTS,
    will_inherit=True,
)

_TEXT_ALIGNMENTS = [
    ("left", _("Left")),
    ("center", _("Center")),
    ("right", _("Right")),
    ("justify", _("Justify")),
]

TEXT_ALIGN_CHOICES = make_choices(
    "text-",
    _TEXT_ALIGNMENTS,
    will_inherit=True,
)

_LINE_HEIGHTS = [
    ("none", "none (1)"),
    ("tight", "tight (1.25)"),
    ("snug", "snug (1.375)"),
    ("normal", "normal (1.5)"),
    ("relaxed", "relaxed (1.625)"),
    ("loose", "loose (2)"),
]

LINE_HEIGHT_CHOICES = make_choices(
    "leading-",
    _LINE_HEIGHTS,
    will_inherit=True,
)

_LETTER_SPACING = [
    ("tighter", "tighter (-0.05em)"),
    ("tight", "tight (-0.025em)"),
    ("normal", "normal (0)"),
    ("wide", "wide (0.025em)"),
    ("wider", "wider (0.05em)"),
    ("widest", "widest (0.1em)"),
]

LETTER_SPACING_CHOICES = make_choices(
    "tracking-",
    _LETTER_SPACING,
    will_inherit=True,
)

FONT_FAMILY_ROLE_CHOICES = [
    ("heading", "Heading"),
    ("subheading", "Subheading"),
    ("body", "Body"),
    ("code", "Code"),
    ("custom", "Custom"),
]

GENERIC_FONT_FAMILY_CHOICES = [
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
]
