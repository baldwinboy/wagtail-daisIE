from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import DAISYUI_BG_COLOR_CHOICES
from wagtail_daisIE.widgets import DaisyUISwatchWidget

from .css import build_background_css, merge_block_css
from .fields import ColorChoiceBlock


class TextBackgroundBlock(blocks.StructBlock):
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


class BackgroundBlock(TextBackgroundBlock):
    bg_image = blocks.ChoiceBlock(
        choices=[
            ("", _("None")),
            ("bg-cover", _("Cover")),
            ("bg-contain", _("Contain")),
        ],
        default="",
        required=False,
        label=_("Background image mode"),
    )

    class Meta:
        icon = "image"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "bg_color",
                "bg_image",
            ],
            heading=_("Background"),
        )
