"""A block that renders an admin-designed, reusable content snippet.

The ``wagtail_daisIE.ReusableBlock`` snippet stores a designed stream of page
content blocks. This chooser references it and renders its blocks at the
insertion point with the current render context (theme, design channels,
request, context bindings), so editing the snippet updates every page, form,
menu or feed item card that imports it.

The snippet's content excludes this chooser, so a reusable block can never
contain itself and references cannot recurse.
"""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.snippets.blocks import SnippetChooserBlock

from ..base_blocks import ThemedBlock


class ReusableBlockBlock(ThemedBlock):
    """Reference a saved :class:`~wagtail_daisIE.models.ReusableBlock`."""

    reusable = SnippetChooserBlock("wagtail_daisIE.ReusableBlock")

    class Meta:
        icon = "doc-full-inverse"
        group = _("Reusable")
        label = _("Reusable block")
        collapsed = True
        template = "wagtail_daisIE/blocks/reusable.html"
        form_layout = blocks.BlockGroup(
            children=["reusable"],
            settings=["design", "audience"],
        )
