from .utils import make_auto_spacing_choices, make_spacing_choices


PADDING_CHOICES = {
    "ALL": make_spacing_choices("p-"),
    "TOP": make_spacing_choices("pt-"),
    "RIGHT": make_spacing_choices("pr-"),
    "BOTTOM": make_spacing_choices("pb-"),
    "LEFT": make_spacing_choices("pl-"),
}

MARGIN_CHOICES = {
    "ALL": make_auto_spacing_choices("m-"),
    "TOP": make_auto_spacing_choices("mt-"),
    "RIGHT": make_auto_spacing_choices("mr-"),
    "BOTTOM": make_auto_spacing_choices("mb-"),
    "LEFT": make_auto_spacing_choices("ml-"),
}

GAP_CHOICES = {
    "ALL": make_spacing_choices("gap-"),
    "HORIZONTAL": make_spacing_choices("gap-x-"),
    "VERTICAL": make_spacing_choices("gap-y-"),
}
