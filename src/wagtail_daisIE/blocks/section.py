from wagtail import blocks

from ..base_blocks import ContentAlignmentBlock, ThemedSpacedBlock


class SectionBlock(ThemedSpacedBlock):
    """A themed container that can be aligned left/right/centre.

    Content alignment lives in the settings panel (via
    :class:`~wagtail_daisIE.base_blocks.ContentAlignmentBlock`) rather than
    being spread across the content fields.
    """

    alignment = ContentAlignmentBlock()

    class Meta:
        abstract = True
        form_layout = blocks.BlockGroup(
            children=[],
            settings=["design", "alignment", "audience"],
        )
