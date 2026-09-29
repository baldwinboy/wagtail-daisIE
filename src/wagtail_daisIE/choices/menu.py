from django.utils.translation import gettext_lazy as _

from .utils import ChoiceList


MENU_SIZE_CHOICES = ChoiceList(
    [
        ("", _("Default")),
        ("menu-xs", "xs"),
        ("menu-sm", "sm"),
        ("menu-md", "md"),
        ("menu-lg", "lg"),
        ("menu-xl", "xl"),
    ],
    "MENU_SIZE_CHOICES",
)
