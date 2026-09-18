from django.utils.translation import gettext_lazy as _


TABLE_BORDER_CHOICES = [
    ("", _("Default")),
    ("border-collapse", _("Collapse (single border)")),
    ("border-separate", _("Separate (double border)")),
]

TABLE_LAYOUT_CHOICES = [
    ("", _("Default")),
    ("table-auto", _("Auto (fit to content)")),
    ("table-fixed", _("Fixed (each column has equal width)")),
]

TABLE_CAPTION_CHOICES = [
    ("", _("Default")),
    ("caption-top", _("Top")),
    ("caption-bottom", _("Bottom")),
]

TABLE_SIZE_CHOICES = [
    ("", _("Default")),
    ("table-xs", _("xs")),
    ("table-sm", _("sm")),
    ("table-md", _("md")),
    ("table-lg", _("lg")),
    ("table-xl", _("xl")),
]
