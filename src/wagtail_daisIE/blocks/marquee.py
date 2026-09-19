from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from .section import SectionBlock


class MarqueeBlock(SectionBlock):
    SPEED_CHOICES = [
        ("animate-[marquee_30s_linear_infinite]", _("Slow")),
        ("animate-[marquee_20s_linear_infinite]", _("Medium")),
        ("animate-[marquee_10s_linear_infinite]", _("Fast")),
    ]

    DIRECTION_CHOICES = [
        ("flex-row", _("Left to right")),
        ("flex-row-reverse", _("Right to left")),
    ]

    text = blocks.CharBlock(
        max_length=255,
        help_text=_("Text content for the marquee."),
        blank=True,
    )
    speed = blocks.ChoiceBlock(
        choices=SPEED_CHOICES,
        default="animate-[marquee_20s_linear_infinite]",
        help_text=_("Speed of the marquee animation."),
    )
    direction = blocks.ChoiceBlock(
        choices=DIRECTION_CHOICES,
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
