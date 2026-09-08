from django.utils.translation import gettext_lazy as _

from .utils import make_choices


_SHADOW_SIZES = [
    ("2xs", _("Smallest")),
    ("xs", _("Smaller")),
    ("sm", _("Small")),
    ("md", _("Medium")),
    ("lg", _("Large")),
    ("xl", _("Larger")),
    ("2xl", _("Largest")),
]

SHADOW_CHOICES = make_choices("shadow-", _SHADOW_SIZES)
