from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices import ALIGNMENT_CHOICES, JUSTIFY_CHOICES


class ContentAlignmentBlock(blocks.StructBlock):
    """Alignment of the content inside a section or container block.

    This block is meant to be placed in the ``settings`` area of a themed
    block's form layout rather than rendered inline with the content fields.
    """

    content_align = blocks.ChoiceBlock(
        choices=ALIGNMENT_CHOICES,
        default="",
        required=False,
        label=_("Content alignment"),
        help_text=_("Vertical alignment of the content."),
    )
    content_justify = blocks.ChoiceBlock(
        choices=JUSTIFY_CHOICES,
        default="",
        required=False,
        label=_("Content justification"),
        help_text=_("Horizontal justification of the content."),
    )

    class Meta:
        icon = "grip"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "content_align",
                "content_justify",
            ],
            heading=_("Content alignment"),
        )
