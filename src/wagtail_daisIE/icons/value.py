import re

from dataclasses import dataclass


PREFIX_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:[-_.][a-z0-9]+)*$")

DEFAULT_ICONIFY_COLLECTIONS = [
    "mdi",
    "fa6-solid",
    "fa6-regular",
    "fa6-brands",
    "lucide",
    "heroicons",
    "bootstrap",
    "material-symbols",
]


class IconValueError(ValueError):
    """Raised when an icon identifier is malformed."""


@dataclass(frozen=True)
class IconValue:
    prefix: str
    name: str

    def __str__(self):
        return f"{self.prefix}:{self.name}"

    @property
    def is_wagtail(self):
        return self.prefix == "wagtail"


def split_icon(value):
    """Split a stored icon value into ``(prefix, name)``.

    Returns ``(None, raw)`` for legacy raw-class values and ``(None, None)``
    for empty input.
    """
    if value is None:
        return None, None
    value = str(value).strip()
    if not value:
        return None, None
    if ":" in value:
        prefix, _, name = value.partition(":")
        return prefix.strip(), name.strip()
    return None, value


def is_legacy(value):
    return ":" not in (value or "")


def validate_icon(value):
    """Validate a universal icon value, returning an :class:`IconValue`.

    Legacy raw-class values are rejected (use :func:`is_legacy` for those).
    """
    prefix, name = split_icon(value)
    if not prefix or not name:
        raise IconValueError(f"Invalid icon value: {value!r}")
    if not PREFIX_PATTERN.match(prefix):
        raise IconValueError(f"Invalid icon prefix: {prefix!r}")
    if not NAME_PATTERN.match(name):
        raise IconValueError(f"Invalid icon name: {name!r}")
    return IconValue(prefix, name)
