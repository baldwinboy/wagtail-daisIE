"""A block that renders an admin-designed, reusable content snippet.

The ``wagtail_daisIE.ReusableBlock`` snippet stores a designed stream of page
content blocks. This chooser references it and renders its blocks at the
insertion point with the current render context (theme, design channels,
request, context bindings), so editing the snippet updates every page, form,
menu or feed item card that imports it.

The snippet's content excludes this chooser at its top level, so the library
cannot reference itself directly. A reusable block can still be reached
indirectly through a container, so rendering is guarded against cycles and
validation rejects a direct self-reference.
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.snippets.blocks import SnippetChooserBlock

from ..base_blocks import ThemedBlock
from ..dynamic.recursion import guard_render, iter_nested_stream_blocks


class ReusableBlockBlock(ThemedBlock):
    """Reference a saved :class:`~wagtail_daisIE.models.ReusableBlock`."""

    reusable = SnippetChooserBlock("wagtail_daisIE.ReusableBlock")

    class Meta:
        icon = "doc-full-inverse"
        group = _("Layout")
        label = _("Reusable block")
        collapsed = True
        template = "wagtail_daisIE/blocks/reusable.html"
        form_layout = blocks.BlockGroup(
            children=["reusable"],
            settings=["design", "audience"],
        )

    def render(self, value, context=None):
        reusable = (value or {}).get("reusable")
        pk = getattr(reusable, "pk", None)
        if pk is None:
            return super().render(value, context)
        with guard_render("reusable", pk) as allowed:
            if not allowed:
                return ""
            return super().render(value, context)

    def clean(self, value):
        value = super().clean(value)
        reusable = value.get("reusable")
        pk = getattr(reusable, "pk", None)
        if pk is not None:
            for block_type, child in iter_nested_stream_blocks(reusable.content):
                if block_type != "reusable":
                    continue
                nested = getattr(child.get("reusable"), "pk", None)
                if nested == pk:
                    raise ValidationError(_("A reusable block cannot include itself."))
        return value
