from .utils import ChoiceList, make_auto_spacing_choices, make_spacing_choices


PADDING_ALL_CHOICES = ChoiceList(make_spacing_choices("p-"), "PADDING_ALL_CHOICES")
PADDING_TOP_CHOICES = ChoiceList(make_spacing_choices("pt-"), "PADDING_TOP_CHOICES")
PADDING_RIGHT_CHOICES = ChoiceList(make_spacing_choices("pr-"), "PADDING_RIGHT_CHOICES")
PADDING_BOTTOM_CHOICES = ChoiceList(
    make_spacing_choices("pb-"), "PADDING_BOTTOM_CHOICES"
)
PADDING_LEFT_CHOICES = ChoiceList(make_spacing_choices("pl-"), "PADDING_LEFT_CHOICES")
PADDING_CHOICES = {
    "ALL": PADDING_ALL_CHOICES,
    "TOP": PADDING_TOP_CHOICES,
    "RIGHT": PADDING_RIGHT_CHOICES,
    "BOTTOM": PADDING_BOTTOM_CHOICES,
    "LEFT": PADDING_LEFT_CHOICES,
}

MARGIN_ALL_CHOICES = ChoiceList(make_auto_spacing_choices("m-"), "MARGIN_ALL_CHOICES")
MARGIN_TOP_CHOICES = ChoiceList(make_auto_spacing_choices("mt-"), "MARGIN_TOP_CHOICES")
MARGIN_RIGHT_CHOICES = ChoiceList(
    make_auto_spacing_choices("mr-"), "MARGIN_RIGHT_CHOICES"
)
MARGIN_BOTTOM_CHOICES = ChoiceList(
    make_auto_spacing_choices("mb-"), "MARGIN_BOTTOM_CHOICES"
)
MARGIN_LEFT_CHOICES = ChoiceList(
    make_auto_spacing_choices("ml-"), "MARGIN_LEFT_CHOICES"
)
MARGIN_CHOICES = {
    "ALL": MARGIN_ALL_CHOICES,
    "TOP": MARGIN_TOP_CHOICES,
    "RIGHT": MARGIN_RIGHT_CHOICES,
    "BOTTOM": MARGIN_BOTTOM_CHOICES,
    "LEFT": MARGIN_LEFT_CHOICES,
}

GAP_ALL_CHOICES = ChoiceList(make_spacing_choices("gap-"), "GAP_ALL_CHOICES")
GAP_HORIZONTAL_CHOICES = ChoiceList(
    make_spacing_choices("gap-x-"), "GAP_HORIZONTAL_CHOICES"
)
GAP_VERTICAL_CHOICES = ChoiceList(
    make_spacing_choices("gap-y-"), "GAP_VERTICAL_CHOICES"
)
GAP_CHOICES = {
    "ALL": GAP_ALL_CHOICES,
    "HORIZONTAL": GAP_HORIZONTAL_CHOICES,
    "VERTICAL": GAP_VERTICAL_CHOICES,
}
