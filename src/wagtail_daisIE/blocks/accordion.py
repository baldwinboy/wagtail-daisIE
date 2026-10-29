from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks.compact import DaisieStructBlock
from .inline import HeaderBlock
from .section import SectionBlock
from .stream import AccordionItemContentStreamBlock


class AccordionItemBlock(DaisieStructBlock):
    heading = HeaderBlock()
    content = AccordionItemContentStreamBlock()
    collapsed = blocks.BooleanBlock(
        default=True,
        required=False,
        label=_("Start collapsed"),
    )

    class Meta:
        icon = "plus"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/accordion_item.html"
        form_layout = blocks.BlockGroup(
            children=["heading", "content", "collapsed"],
        )


class AccordionBlock(SectionBlock):
    items = blocks.ListBlock(AccordionItemBlock(), label=_("Accordion items"))

    class Meta:
        icon = "placeholder"
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/blocks/accordion.html"
        form_layout = blocks.BlockGroup(
            children=["items"],
            settings=["design", "alignment", "audience"],
        )
