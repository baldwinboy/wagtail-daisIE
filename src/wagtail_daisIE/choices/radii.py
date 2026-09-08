from django.utils.translation import gettext_lazy as _

from .utils import make_choices


_ROUNDED_SIZES = [
    ("xs", _("Smallest")),
    ("sm", _("Small")),
    ("md", _("Medium")),
    ("lg", _("Large")),
    ("xl", _("Larger")),
    ("2xl", _("Largest")),
    ("3xl", _("Extra large")),
    ("4xl", _("Extra extra large")),
    ("full", _("Full")),
]

ROUNDED_CHOICES = make_choices("rounded-", _ROUNDED_SIZES)
