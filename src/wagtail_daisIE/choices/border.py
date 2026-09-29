from django.utils.translation import gettext_lazy as _

from .utils import ChoiceList


BORDER_STYLE_CHOICES = ChoiceList(
    [
        ("", _("Default")),
        ("solid", _("Solid")),
        ("dashed", _("Dashed")),
        ("dotted", _("Dotted")),
        ("double", _("Double")),
        ("none", _("None")),
    ],
    "BORDER_STYLE_CHOICES",
)
