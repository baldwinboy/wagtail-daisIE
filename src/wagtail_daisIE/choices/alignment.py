from django.utils.translation import gettext_lazy as _

from .utils import ChoiceList


ALIGNMENT_CHOICES = ChoiceList(
    [
        ("", _("Default")),
        ("items-start", _("Top / Start")),
        ("items-center", _("Center")),
        ("items-end", _("Bottom / End")),
        ("items-stretch", _("Stretch")),
    ],
    "ALIGNMENT_CHOICES",
)

JUSTIFY_CHOICES = ChoiceList(
    [
        *ALIGNMENT_CHOICES,
        ("justify-between", _("Space between")),
        ("justify-around", _("Space around")),
        ("justify-evenly", _("Space evenly")),
    ],
    "JUSTIFY_CHOICES",
)
