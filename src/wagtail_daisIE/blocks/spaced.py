from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks.compact import DaisieStreamBlock
from ..choicelist import ChoiceList
from .cards import CONTENT_BLOCKS
from .icons import IconChooserBlock
from .inline import HeaderBlock
from .link import InlineLinkBlock
from .section import SectionBlock


LIST_ORDERING_CHOICES = ChoiceList(
    [
        ("list-none", _("Unordered")),
        ("list-decimal", _("Ordered")),
    ],
    "LIST_ORDERING_CHOICES",
)


class SpacedBlock(SectionBlock):
    content = DaisieStreamBlock(
        CONTENT_BLOCKS,
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
        choices=LIST_ORDERING_CHOICES,
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
    content = DaisieStreamBlock(
        LIST_CONTENT_BLOCKS,
    )

    class Meta:
        abstract = True
