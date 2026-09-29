from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import DAISYUI_BG_COLOR_CHOICES
from wagtail_daisIE.widgets import DaisyUISwatchWidget

from .css import build_background_css, merge_block_css
from .fields import ColorChoiceBlock


class TextBackgroundBlock(blocks.StructBlock):
    """Solid-colour background.

    The web design pipeline uses :class:`BackgroundStreamBlock` instead, so
    images and gradients are available. This block is retained for the email
    components that only accept a background colour (``container-background-color``
    or ``background-color``); see ``emails/blocks/design.py``.
    """

    bg_color = ColorChoiceBlock(
        choices=DAISYUI_BG_COLOR_CHOICES,
        default="",
        required=False,
        label=_("Background color"),
        widget=DaisyUISwatchWidget(prefix="bg"),
    )

    class Meta:
        icon = "doc-empty-inverse"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "bg_color",
            ],
            heading=_("Background"),
        )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["block_css"] = merge_block_css(
            parent_context, build_background_css(value)
        )
        return context
