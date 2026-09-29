from django.utils.translation import gettext_lazy as _

from .utils import ChoiceList


TABLE_BORDER_CHOICES = ChoiceList(
    [
        ("", _("Default")),
        ("border-collapse", _("Collapse (single border)")),
        ("border-separate", _("Separate (double border)")),
    ],
    "TABLE_BORDER_CHOICES",
)

TABLE_LAYOUT_CHOICES = ChoiceList(
    [
        ("", _("Default")),
        ("table-auto", _("Auto (fit to content)")),
        ("table-fixed", _("Fixed (each column has equal width)")),
    ],
    "TABLE_LAYOUT_CHOICES",
)

TABLE_CAPTION_CHOICES = ChoiceList(
    [
        ("", _("Default")),
        ("caption-top", _("Top")),
        ("caption-bottom", _("Bottom")),
    ],
    "TABLE_CAPTION_CHOICES",
)

TABLE_SIZE_CHOICES = ChoiceList(
    [
        ("", _("Default")),
        ("table-xs", _("xs")),
        ("table-sm", _("sm")),
        ("table-md", _("md")),
        ("table-lg", _("lg")),
        ("table-xl", _("xl")),
    ],
    "TABLE_SIZE_CHOICES",
)
