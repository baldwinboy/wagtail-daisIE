from django.utils.translation import gettext_lazy as _


ALIGNMENT_CHOICES = [
    ("", _("Default")),
    ("items-start", _("Top / Start")),
    ("items-center", _("Center")),
    ("items-end", _("Bottom / End")),
    ("items-stretch", _("Stretch")),
]

JUSTIFY_CHOICES = [
    *ALIGNMENT_CHOICES,
    ("justify-between", _("Space between")),
    ("justify-around", _("Space around")),
    ("justify-evenly", _("Space evenly")),
]
