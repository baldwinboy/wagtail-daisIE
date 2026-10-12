"""Top-level email content stream.

Only components that are valid direct children of ``mj-body`` live here; the
section block wraps its own content in an ``mj-column``.
"""

from django.utils.translation import gettext_lazy as _

from ...base_blocks.compact import DaisieStreamBlock
from .layout import EmailHeroBlock, EmailSectionBlock, EmailWrapperBlock
from .leaves import EmailRawBlock
from .reusable import EmailReusableBlockBlock


#: Blocks that may be placed directly on the email body.
EMAIL_BODY_BLOCKS = [
    ("section", EmailSectionBlock()),
    ("wrapper", EmailWrapperBlock()),
    ("hero", EmailHeroBlock()),
    ("raw", EmailRawBlock()),
]

#: Blocks an admin may save into a reusable email snippet. Captured before the
#: reusable chooser is appended, so the library cannot reference itself.
EMAIL_REUSABLE_CONTENT_BLOCKS = list(EMAIL_BODY_BLOCKS)

#: Referencing a saved email snippet is itself a body-level block.
EMAIL_BODY_BLOCKS.append(("reusable", EmailReusableBlockBlock()))


class EmailContentBlock(DaisieStreamBlock):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("local_blocks", EMAIL_BODY_BLOCKS)
        super().__init__(*args, **kwargs)

    class Meta:
        icon = "mail"
        label = _("Email content")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/content.html"
