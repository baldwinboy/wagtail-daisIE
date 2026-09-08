import re

from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


COLOR_HEX_OR_HEXA_RE = re.compile(
    r"^(#[0-9A-Fa-f]{3}|#[0-9A-Fa-f]{4}|#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{8})$"
)
color_hex_or_hexa_validator = RegexValidator(
    COLOR_HEX_OR_HEXA_RE,
    _("Enter a valid hex or hexa color, e.g. #000000 or #00000000"),
    "invalid",
)
