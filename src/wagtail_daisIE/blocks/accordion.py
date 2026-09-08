from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from .cards import CONTENT_BLOCKS
from .inline import HeaderBlock
from .section import SectionBlock


class AccordionItemBlock(blocks.StructBlock):
    heading = HeaderBlock()
    content = blocks.StreamBlock(
        CONTENT_BLOCKS,
        label=_("Accordion item content"),
    )
    collapsed = blocks.BooleanBlock(
        default=True,
        required=False,
        label=_("Start collapsed"),
    )

    class Meta:
        icon = "plus"
        group = _("Accordion Item")
        collapsed = True
        template = "wagtail_daisIE/blocks/accordion_item.html"


class AccordionBlock(SectionBlock):
    items = blocks.ListBlock(AccordionItemBlock(), label=_("Accordion items"))

    class Meta:
        icon = "placeholder"
        group = _("Accordion")
        collapsed = True
        template = "wagtail_daisIE/blocks/accordion.html"
        form_layout = blocks.BlockGroup(
            children=["items"],
            settings=["design", "alignment", "audience"],
        )
