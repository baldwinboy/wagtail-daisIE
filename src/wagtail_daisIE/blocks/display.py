"""Data-display component blocks (badge, kbd, divider, avatar, stat, ...)."""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.images.blocks import ImageBlock as WagtailImageBlock

from ..base_blocks import InlineMarkupBlock, ThemedBlock, ThemedTypographyBlock
from ..choicelist import ChoiceList
from ..choices import (
    ASPECT_RATIO_CHOICES,
    AVATAR_SHAPE_CHOICES,
    AVATAR_SIZE_CHOICES,
    AVATAR_STATUS_CHOICES,
    BADGE_COLOR_CHOICES,
    BADGE_SIZE_CHOICES,
    BADGE_STYLE_CHOICES,
    BLOCK_HEIGHT_CHOICES,
    BLOCK_WIDTH_CHOICES,
    COUNTDOWN_SIZE_CHOICES,
    DIVIDER_COLOR_CHOICES,
    DIVIDER_ORIENTATION_CHOICES,
    DIVIDER_POSITION_CHOICES,
    SKELETON_SHAPE_CHOICES,
    STAT_COLOR_CHOICES,
)
from ..icons.blocks import IconChooserBlock


CHAT_POSITION_CHOICES = ChoiceList(
    [
        ("chat-start", _("Start")),
        ("chat-end", _("End")),
    ],
    "CHAT_POSITION_CHOICES",
)


class BadgeBlock(ThemedTypographyBlock):
    text = InlineMarkupBlock(max_length=64)
    color = blocks.ChoiceBlock(choices=BADGE_COLOR_CHOICES, default="", required=False)
    style = blocks.ChoiceBlock(choices=BADGE_STYLE_CHOICES, default="", required=False)
    size = blocks.ChoiceBlock(choices=BADGE_SIZE_CHOICES, default="", required=False)

    class Meta:
        icon = "tag"
        group = _("Display")
        collapsed = True
        template = "wagtail_daisIE/blocks/display/badge.html"
        form_layout = blocks.BlockGroup(
            children=["text", "color", "style", "size"],
            settings=["design", "audience"],
        )


class KbdBlock(ThemedTypographyBlock):
    text = InlineMarkupBlock(max_length=64)

    class Meta:
        icon = "keyboard"
        group = _("Display")
        collapsed = True
        template = "wagtail_daisIE/blocks/display/kbd.html"
        form_layout = blocks.BlockGroup(
            children=["text"],
            settings=["design", "audience"],
        )


class DividerBlock(ThemedBlock):
    text = InlineMarkupBlock(max_length=64, required=False, blank=True)
    color = blocks.ChoiceBlock(
        choices=DIVIDER_COLOR_CHOICES, default="", required=False
    )
    position = blocks.ChoiceBlock(
        choices=DIVIDER_POSITION_CHOICES,
        default="",
        required=False,
    )
    orientation = blocks.ChoiceBlock(
        choices=DIVIDER_ORIENTATION_CHOICES,
        default="",
        required=False,
    )

    class Meta:
        icon = "horizontalrule"
        group = _("Display")
        collapsed = True
        template = "wagtail_daisIE/blocks/display/divider.html"
        form_layout = blocks.BlockGroup(
            children=["text", "color", "position", "orientation"],
            settings=["design", "audience"],
        )


class AvatarBlock(ThemedBlock):
    image = WagtailImageBlock(required=False)
    size = blocks.ChoiceBlock(choices=AVATAR_SIZE_CHOICES, default="", required=False)
    shape = blocks.ChoiceBlock(choices=AVATAR_SHAPE_CHOICES, default="", required=False)
    status = blocks.ChoiceBlock(
        choices=AVATAR_STATUS_CHOICES, default="", required=False
    )

    class Meta:
        icon = "user"
        group = _("Display")
        collapsed = True
        template = "wagtail_daisIE/blocks/display/avatar.html"
        form_layout = blocks.BlockGroup(
            children=["image", "size", "shape", "status"],
            settings=["design", "audience"],
        )


class StatBlock(ThemedBlock):
    title = InlineMarkupBlock(max_length=128, required=False, blank=True)
    value = InlineMarkupBlock(max_length=128)
    description = InlineMarkupBlock(max_length=255, required=False, blank=True)
    color = blocks.ChoiceBlock(
        choices=STAT_COLOR_CHOICES, default="", required=False, label=_("Value color")
    )

    class Meta:
        icon = "plus-inverse"
        group = _("Display")
        collapsed = True
        template = "wagtail_daisIE/blocks/display/stat.html"
        form_layout = blocks.BlockGroup(
            children=["title", "value", "description", "color"],
            settings=["design", "audience"],
        )


class CountdownBlock(ThemedBlock):
    value = blocks.IntegerBlock(min_value=0, max_value=999, default=0)
    size = blocks.ChoiceBlock(
        choices=COUNTDOWN_SIZE_CHOICES, default="", required=False
    )

    class Meta:
        icon = "time"
        group = _("Display")
        collapsed = True
        template = "wagtail_daisIE/blocks/display/countdown.html"
        form_layout = blocks.BlockGroup(
            children=["value", "size"],
            settings=["design", "audience"],
        )


class SkeletonBlock(ThemedBlock):
    shape = blocks.ChoiceBlock(choices=SKELETON_SHAPE_CHOICES, default="skeleton")
    width = blocks.ChoiceBlock(choices=BLOCK_WIDTH_CHOICES, default="", required=False)
    height = blocks.ChoiceBlock(
        choices=BLOCK_HEIGHT_CHOICES, default="", required=False
    )

    class Meta:
        icon = "placeholder"
        group = _("Display")
        collapsed = True
        template = "wagtail_daisIE/blocks/display/skeleton.html"
        form_layout = blocks.BlockGroup(
            children=["shape", "width", "height"],
            settings=["design", "audience"],
        )


class TextRotateBlock(ThemedBlock):
    texts = blocks.ListBlock(
        InlineMarkupBlock(max_length=255, label=_("Line")),
        label=_("Lines"),
        help_text=_("Up to 6 lines shown one at a time."),
    )

    class Meta:
        icon = "repeat"
        group = _("Display")
        collapsed = True
        template = "wagtail_daisIE/blocks/display/text_rotate.html"
        form_layout = blocks.BlockGroup(
            children=["texts"],
            settings=["design", "audience"],
        )


class ChatMessageBlock(blocks.StructBlock):
    position = blocks.ChoiceBlock(
        choices=CHAT_POSITION_CHOICES,
        default="chat-start",
        label=_("Side"),
    )
    name = InlineMarkupBlock(max_length=64, required=False, blank=True)
    time = InlineMarkupBlock(max_length=64, required=False, blank=True)
    text = InlineMarkupBlock(max_length=500, label=_("Message"))
    avatar = WagtailImageBlock(required=False)

    class Meta:
        icon = "comment"
        label = _("Message")
        collapsed = True


class ChatBlock(ThemedBlock):
    messages = blocks.ListBlock(ChatMessageBlock())

    class Meta:
        icon = "comment"
        group = _("Display")
        collapsed = True
        template = "wagtail_daisIE/blocks/display/chat.html"
        form_layout = blocks.BlockGroup(
            children=["messages"],
            settings=["design", "audience"],
        )


class TimelineItemBlock(blocks.StructBlock):
    start = InlineMarkupBlock(max_length=255, required=False, blank=True)
    end = InlineMarkupBlock(max_length=255, required=False, blank=True)
    icon = IconChooserBlock(required=False, label=_("Marker icon"))

    class Meta:
        icon = "time"
        label = _("Event")
        collapsed = True


class TimelineBlock(ThemedBlock):
    items = blocks.ListBlock(TimelineItemBlock(), label=_("Events"))
    vertical = blocks.BooleanBlock(default=True, required=False)

    class Meta:
        icon = "time"
        group = _("Display")
        collapsed = True
        template = "wagtail_daisIE/blocks/display/timeline.html"
        form_layout = blocks.BlockGroup(
            children=["items", "vertical"],
            settings=["design", "audience"],
        )


class DiffBlock(ThemedBlock):
    before = WagtailImageBlock(label=_("Before image"))
    after = WagtailImageBlock(label=_("After image"))
    aspect = blocks.ChoiceBlock(
        choices=ASPECT_RATIO_CHOICES,
        default="",
        required=False,
        label=_("Aspect ratio"),
    )

    class Meta:
        icon = "image"
        group = _("Media")
        collapsed = True
        template = "wagtail_daisIE/blocks/display/diff.html"
        form_layout = blocks.BlockGroup(
            children=["before", "after", "aspect"],
            settings=["design", "audience"],
        )


class HoverGalleryBlock(ThemedBlock):
    images = blocks.ListBlock(
        WagtailImageBlock(label=_("Image")),
        help_text=_("Up to 10 images; the first is visible until hover."),
    )

    class Meta:
        icon = "image"
        group = _("Media")
        collapsed = True
        template = "wagtail_daisIE/blocks/display/hover_gallery.html"
        form_layout = blocks.BlockGroup(
            children=["images"],
            settings=["design", "audience"],
        )


class Hover3DCardBlock(ThemedBlock):
    image = WagtailImageBlock()
    caption = blocks.CharBlock(max_length=255, required=False, blank=True)

    class Meta:
        icon = "image"
        group = _("Media")
        collapsed = True
        template = "wagtail_daisIE/blocks/display/hover_3d.html"
        form_layout = blocks.BlockGroup(
            children=["image", "caption"],
            settings=["design", "audience"],
        )


__all__ = [
    "AvatarBlock",
    "BadgeBlock",
    "ChatBlock",
    "ChatMessageBlock",
    "CountdownBlock",
    "DiffBlock",
    "DividerBlock",
    "Hover3DCardBlock",
    "HoverGalleryBlock",
    "KbdBlock",
    "SkeletonBlock",
    "StatBlock",
    "TextRotateBlock",
    "TimelineBlock",
    "TimelineItemBlock",
]
