"""Top-level email content stream.

Only components that are valid direct children of ``mj-body`` live here; the
section block wraps its own content in an ``mj-column``.
"""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from .layout import EmailSectionBlock
from .leaves import EmailRawBlock


#: Blocks that may be placed directly on the email body.
EMAIL_BODY_BLOCKS = [
    ("section", EmailSectionBlock()),
    ("raw", EmailRawBlock()),
]


class EmailContentBlock(blocks.StreamBlock):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("local_blocks", EMAIL_BODY_BLOCKS)
        super().__init__(*args, **kwargs)

    class Meta:
        icon = "mail"
        label = _("Email content")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/content.html"
