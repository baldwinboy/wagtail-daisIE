from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from wagtail.blocks.field_block import FieldBlock

from .fields import IconBlockField


class IconChooserBlock(FieldBlock):
    """A universal icon chooser block, usable in page StreamFields."""

    def __init__(self, required=True, help_text=None, search_index=True, **kwargs):
        self.search_index = search_index
        self.field = IconBlockField(required=required, help_text=help_text)
        super().__init__(**kwargs)

    def get_searchable_content(self, value):
        return [force_str(value)] if self.search_index else []

    class Meta:
        icon = "image"
        label = _("Icon")
        template = "wagtail_daisIE/blocks/icon.html"
        collapsed = True
