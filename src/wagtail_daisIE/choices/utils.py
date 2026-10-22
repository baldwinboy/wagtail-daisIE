from fractions import Fraction

from django.utils.translation import gettext_lazy as _

from ..choicelist import ChoiceList, get_choice_list  # noqa: F401


# The default Tailwind spacing suffixes (values after the side prefix, e.g. "8" in "pt-8")
_DEFAULT_SPACING_SUFFIXES = [
    "0",
    "px",
    "0.5",
    "1",
    "1.5",
    "2",
    "2.5",
    "3",
    "3.5",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "14",
    "16",
    "20",
    "24",
    "28",
    "32",
    "36",
    "40",
    "44",
    "48",
    "52",
    "56",
    "60",
    "64",
    "72",
    "80",
    "96",
]


def make_choices(
    prefix, suffix_label_pairs, prepend_none=True, will_inherit=False
) -> list[tuple[str, str]]:
    """Prepend a None option and prefix each Tailwind suffix."""
    choices = [(f"{prefix}{suffix}", label) for suffix, label in suffix_label_pairs]

    if prepend_none:
        return [
            (
                "",
                _("None (inherit)" if will_inherit else "None"),
            ),
            *choices,
        ]

    return choices


def make_spacing_choices(prefix, prepend_none=True):
    """Build choices for a given spacing prefix (e.g. 'pt-')."""
    # Use the suffix itself as the human-readable label
    return make_choices(
        prefix, [(s, s) for s in _DEFAULT_SPACING_SUFFIXES], prepend_none
    )


def make_auto_spacing_choices(prefix):
    """Build choices for a given spacing prefix (e.g. 'mt-') with an "auto" option."""
    choices = make_spacing_choices(prefix, prepend_none=False)
    return [
        ("", _("None")),
        (f"{prefix}auto", _("Auto")),
        *choices,
    ]


_AUTO_UTILITY_PREFIXES = (
    "m-",
    "mx-",
    "my-",
    "mt-",
    "mr-",
    "mb-",
    "ml-",
    "w-",
    "h-",
    "size-",
    "min-w-",
    "min-h-",
    "max-w-",
    "max-h-",
)
_AUTO_UTILITY_VALUES = frozenset(f"{prefix}auto" for prefix in _AUTO_UTILITY_PREFIXES)


def is_auto_utility(value):
    """Return whether ``value`` is a legacy or prefixed auto utility class."""
    if not isinstance(value, str):
        return False
    return value == "auto" or value in _AUTO_UTILITY_VALUES


def normalize_auto_class(value, prefix, *, allow_auto=True):
    """Resolve a legacy bare ``"auto"`` to ``<prefix>auto``.

    Prefixed values pass through unchanged. When ``allow_auto`` is false, both
    forms resolve to an empty string (used for max-width/max-height, which have
    no valid auto utility in Tailwind).
    """
    if not isinstance(value, str) or not value:
        return value
    if value == "auto" or value == f"{prefix}auto":
        return f"{prefix}auto" if allow_auto else ""
    return value


def generate_tailwind_fractions(prefix, denominators=(2, 3, 4, 5, 6, 12)):
    """Generate Tailwind fraction utility classes for a given prefix."""
    fractions = []
    for denom in denominators:
        for num in range(1, denom):
            # Skip fractions that are reducible to a simpler form (e.g., 2/4 = 1/2)
            # Tailwind includes them anyway, so we keep them.
            frac = Fraction(num, denom)
            class_name = f"{prefix}{num}/{denom}"
            percentage = f"{float(frac) * 100:.6f}%".rstrip("0").rstrip(".")
            fractions.append((class_name, percentage))
    return fractions


def kebab_to_sentence(str: str) -> str:
    """Convert a kebab-case string to a sentence."""
    return str.replace("-", " ").title().capitalize()
