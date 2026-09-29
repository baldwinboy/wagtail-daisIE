from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks import InlineMarkupBlock
from ..choicelist import ChoiceList
from .section import SectionBlock


MARQUEE_SPEED_CHOICES = ChoiceList(
    [
        ("animate-[marquee_30s_linear_infinite]", _("Slow")),
        ("animate-[marquee_20s_linear_infinite]", _("Medium")),
        ("animate-[marquee_10s_linear_infinite]", _("Fast")),
    ],
    "MARQUEE_SPEED_CHOICES",
)

MARQUEE_DIRECTION_CHOICES = ChoiceList(
    [
        ("flex-row", _("Left to right")),
        ("flex-row-reverse", _("Right to left")),
    ],
    "MARQUEE_DIRECTION_CHOICES",
)


class MarqueeBlock(SectionBlock):
    text = InlineMarkupBlock(
        max_length=255,
        help_text=_("Text content for the marquee."),
        required=False,
    )
    speed = blocks.ChoiceBlock(
        choices=MARQUEE_SPEED_CHOICES,
        default="animate-[marquee_20s_linear_infinite]",
        help_text=_("Speed of the marquee animation."),
    )
    direction = blocks.ChoiceBlock(
        choices=MARQUEE_DIRECTION_CHOICES,
        default="flex-row",
        help_text=_("Direction of the marquee animation."),
    )

    class Meta:
        icon = "horizontalrule"
        group = _("Text")
        collapsed = True
        template = "wagtail_daisIE/blocks/marquee.html"
        form_layout = blocks.BlockGroup(
            children=["text", "speed", "direction"],
            settings=["design", "alignment", "audience"],
        )
