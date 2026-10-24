from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.widgets import DaisyUIIntegerBlock, DaisyUINumberSliderWidget

from ..base_blocks import DaisieStreamBlock
from ..choicelist import ChoiceList
from .inline import InlineTextBlock
from .media import InlineImageBlock
from .section import SectionBlock


MARQUEE_LAYOUT_CHOICES = ChoiceList(
    [
        ("horizontal", _("Horizontal")),
        ("vertical", _("Vertical")),
    ],
    "MARQUEE_LAYOUT_CHOICES",
)


class MarqueeBlock(SectionBlock):
    content = DaisieStreamBlock(
        [
            ("text", InlineTextBlock()),
            ("image", InlineImageBlock()),
        ],
        label=_("Marquee content"),
    )
    speed = DaisyUIIntegerBlock(
        required=False,
        default=5,
        min_value=1,
        max_value=600,
        label=_("Seconds per loop"),
        help_text=_("Higher values are slower."),
        widget=DaisyUINumberSliderWidget(
            min_value=1, max_value=600, step=1, suffix="s"
        ),
    )
    repeat = blocks.BooleanBlock(
        default=True,
        required=False,
        label=_("Repeat content"),
        help_text=_("Content will be duplicated in container, leaving no gap."),
    )
    direction = blocks.ChoiceBlock(
        choices=MARQUEE_LAYOUT_CHOICES,
        default="horizontal",
        label=_("Layout direction"),
    )
    reverse = blocks.BooleanBlock(
        default=False,
        required=False,
        label=_("Reverse direction"),
    )
    pause_on_hover = blocks.BooleanBlock(
        default=False,
        required=False,
        help_text=_("Pause the marquee animation on hover."),
    )
    pause_on_click = blocks.BooleanBlock(
        default=False,
        required=False,
        help_text=_("Pause the marquee animation on click."),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        layout = value.get("direction") or "horizontal"
        if layout not in {"horizontal", "vertical"}:
            layout = "horizontal"
        try:
            speed = int(value.get("speed") or 20)
        except (TypeError, ValueError):
            speed = 20
        speed = max(1, min(speed, 600))

        design = (value or {}).get("design") or {}
        padding = design.get("padding") or {}
        size = design.get("size") or {}
        has_height = bool((size.get("height") or {}).get("height") or size.get("size"))
        css_parts = ["" if any(padding.values()) else "p-4"]
        if layout == "vertical" and not has_height:
            css_parts.append("h-64")

        context["marquee_layout"] = layout
        context["marquee_reverse"] = bool(value.get("reverse"))
        context["marquee_speed"] = speed
        context["marquee_default_css"] = " ".join(part for part in css_parts if part)
        context["marquee_style"] = "; ".join(
            part
            for part in [
                context.get("block_style"),
                f"--daisie-marquee-duration: {speed}s",
            ]
            if part
        )
        return context

    class Meta:
        icon = "media"
        group = _("Media")
        collapsed = True
        template = "wagtail_daisIE/blocks/marquee.html"
        form_layout = blocks.BlockGroup(
            children=["content", "speed", "repeat"],
            settings=[
                "design",
                "alignment",
                "direction",
                "reverse",
                "pause_on_hover",
                "pause_on_click",
                "audience",
            ],
        )
