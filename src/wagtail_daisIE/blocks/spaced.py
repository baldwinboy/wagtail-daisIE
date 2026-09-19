from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from .cards import CONTENT_BLOCKS
from .icons import IconChooserBlock
from .inline import HeaderBlock
from .link import InlineLinkBlock
from .section import SectionBlock


class SpacedBlock(SectionBlock):
    content = blocks.StreamBlock(
        CONTENT_BLOCKS,
        label=_("Content"),
    )

    class Meta:
        abstract = True
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "alignment", "audience"],
        )


class ListBlock(SpacedBlock):
    heading = HeaderBlock(required=False)
    ordering = blocks.ChoiceBlock(
        choices=[
            ("list-none", _("Unordered")),
            ("list-decimal", _("Ordered")),
        ],
        default="list-none",
        help_text=_("Whether the list is ordered or unordered."),
    )

    class Meta:
        icon = "list-ul"
        group = _("List")
        collapsed = True
        template = "wagtail_daisIE/blocks/list.html"
        form_layout = blocks.BlockGroup(
            children=["heading", "content", "ordering"],
            settings=["design", "alignment", "audience"],
        )


class LinkListBlock(SpacedBlock):
    heading = HeaderBlock(required=False)
    content = blocks.ListBlock(InlineLinkBlock(), label=_("Links"))

    class Meta:
        icon = "link"
        group = _("List")
        collapsed = True
        template = "wagtail_daisIE/blocks/list.html"
        form_layout = blocks.BlockGroup(
            children=["heading", "content"],
            settings=["design", "alignment", "audience"],
        )


LIST_CONTENT_BLOCKS = [
    *CONTENT_BLOCKS,
    ("list", ListBlock()),
    ("link_list", LinkListBlock()),
    ("icon", IconChooserBlock()),
]


class SpacedBlockWithList(SpacedBlock):
    content = blocks.StreamBlock(
        LIST_CONTENT_BLOCKS,
        label=_("Content"),
    )

    class Meta:
        abstract = True
