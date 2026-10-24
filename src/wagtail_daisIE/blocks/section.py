from wagtail import blocks

from ..base_blocks import ContentAlignmentBlock, ThemedSpacedBlock
from ..base_blocks.utils import build_class


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

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        alignment = (value or {}).get("alignment") or {}
        alignment_css = build_class(
            alignment.get("content_align", ""),
            alignment.get("content_justify", ""),
        )
        context["alignment_css"] = alignment_css
        context["has_alignment"] = bool(alignment_css)
        return context
