from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import (
    DAISYUI_BUTTON_BEHAVIOR_CHOICES,
    DAISYUI_BUTTON_COLOR_CHOICES,
    DAISYUI_BUTTON_MODIFIER_CHOICES,
    DAISYUI_BUTTON_SIZE_CHOICES,
    DAISYUI_BUTTON_STYLE_CHOICES,
)
from wagtail_daisIE.widgets import DaisyUISwatchWidget

from .fields import ColorChoiceBlock


class ButtonStateBlock(blocks.StructBlock):
    """Base-state styling: what the button looks like normally."""

    color = ColorChoiceBlock(
        choices=DAISYUI_BUTTON_COLOR_CHOICES,
        default="",
        required=False,
        label=_("Color"),
        widget=DaisyUISwatchWidget(prefix="btn-"),
    )
    style = blocks.ChoiceBlock(
        choices=DAISYUI_BUTTON_STYLE_CHOICES,
        default="",
        required=False,
        label=_("Style"),
    )
    size = blocks.ChoiceBlock(
        choices=DAISYUI_BUTTON_SIZE_CHOICES,
        default="",
        required=False,
        label=_("Size"),
    )
    behavior = blocks.ChoiceBlock(
        choices=DAISYUI_BUTTON_BEHAVIOR_CHOICES,
        default="",
        required=False,
        label=_("Behavior"),
    )
    modifier = blocks.ChoiceBlock(
        choices=DAISYUI_BUTTON_MODIFIER_CHOICES,
        default="",
        required=False,
        label=_("Modifier"),
    )

    class Meta:
        collapsed = True


class ButtonAppearanceBlock(blocks.StructBlock):
    """Button appearance: what the button looks like when hovered or active."""

    normal = ButtonStateBlock()
    hover = ButtonStateBlock()
    active = ButtonStateBlock()

    class Meta:
        icon = "palette"
        label = _("Button appearance")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "normal",
                "hover",
                "active",
            ],
            heading=_("Button appearance"),
        )
