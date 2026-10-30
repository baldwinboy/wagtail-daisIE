from django.utils.translation import gettext_lazy as _

from .utils import ChoiceList


LAYOUT_ITEM_GROW_CHOICES = ChoiceList(
    [("", _("Default (inherit)")), ("grow", _("Grow")), ("grow-0", _("Do not grow"))],
    "LAYOUT_ITEM_GROW_CHOICES",
)

LAYOUT_ITEM_SHRINK_CHOICES = ChoiceList(
    [
        ("", _("Default (inherit)")),
        ("shrink", _("Shrink")),
        ("shrink-0", _("Do not shrink")),
    ],
    "LAYOUT_ITEM_SHRINK_CHOICES",
)

LAYOUT_ITEM_BASIS_CHOICES = ChoiceList(
    [
        ("", _("Default (inherit)")),
        ("basis-auto", _("Auto")),
        ("basis-full", _("Full")),
        ("basis-1/2", "1/2"),
        ("basis-1/3", "1/3"),
        ("basis-2/3", "2/3"),
        ("basis-1/4", "1/4"),
        ("basis-3/4", "3/4"),
    ],
    "LAYOUT_ITEM_BASIS_CHOICES",
)

LAYOUT_ITEM_WIDTH_CHOICES = ChoiceList(
    [
        ("", _("Default (inherit)")),
        ("w-auto", _("Auto")),
        ("w-full", _("Full")),
        ("w-fit", _("Fit")),
        ("w-1/2", "1/2"),
        ("w-1/3", "1/3"),
        ("w-2/3", "2/3"),
        ("w-1/4", "1/4"),
        ("w-3/4", "3/4"),
    ],
    "LAYOUT_ITEM_WIDTH_CHOICES",
)

LAYOUT_ITEM_ORDER_CHOICES = ChoiceList(
    [
        ("", _("Default (inherit)")),
        ("order-first", _("First")),
        ("order-last", _("Last")),
        ("order-none", _("DOM order")),
        *[(f"order-{i}", str(i)) for i in range(1, 13)],
    ],
    "LAYOUT_ITEM_ORDER_CHOICES",
)

LAYOUT_ITEM_SELF_ALIGN_CHOICES = ChoiceList(
    [
        ("", _("Default (inherit)")),
        ("self-auto", _("Auto")),
        ("self-start", _("Start")),
        ("self-center", _("Center")),
        ("self-end", _("End")),
        ("self-stretch", _("Stretch")),
        ("self-baseline", _("Baseline")),
    ],
    "LAYOUT_ITEM_SELF_ALIGN_CHOICES",
)

LAYOUT_ITEM_GRID_COLUMN_SPAN_CHOICES = ChoiceList(
    [
        ("", _("Default (inherit)")),
        *[(f"col-span-{i}", str(i)) for i in range(1, 7)],
        ("col-span-full", _("Full")),
    ],
    "LAYOUT_ITEM_GRID_COLUMN_SPAN_CHOICES",
)

LAYOUT_ITEM_GRID_ROW_SPAN_CHOICES = ChoiceList(
    [
        ("", _("Default (inherit)")),
        *[(f"row-span-{i}", str(i)) for i in range(1, 7)],
    ],
    "LAYOUT_ITEM_GRID_ROW_SPAN_CHOICES",
)

LAYOUT_ITEM_JUSTIFY_SELF_CHOICES = ChoiceList(
    [
        ("", _("Default (inherit)")),
        ("justify-self-auto", _("Auto")),
        ("justify-self-start", _("Start")),
        ("justify-self-center", _("Center")),
        ("justify-self-end", _("End")),
        ("justify-self-stretch", _("Stretch")),
    ],
    "LAYOUT_ITEM_JUSTIFY_SELF_CHOICES",
)
