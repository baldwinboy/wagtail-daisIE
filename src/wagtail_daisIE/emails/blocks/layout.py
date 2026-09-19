"""Structural MJML blocks.

MJML only permits ``mj-column`` inside ``mj-section`` and leaf components
inside ``mj-column``. To keep the editor experience close to the web blocks
(one content stream per section) the section template wraps its content in a
single ``mj-column``.
"""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ...blocks.section import SectionBlock
from .base import EmailThemedMixin
from .leaves import (
    EmailButtonBlock,
    EmailDividerBlock,
    EmailHeaderBlock,
    EmailImageBlock,
    EmailLinkBlock,
    EmailRichTextBlock,
    EmailSpacerBlock,
    EmailTextBlock,
)


#: Blocks that may be placed inside an ``mj-column``.
EMAIL_COLUMN_BLOCKS = [
    ("header", EmailHeaderBlock()),
    ("text", EmailTextBlock()),
    ("rich_text", EmailRichTextBlock()),
    ("button", EmailButtonBlock()),
    ("link", EmailLinkBlock()),
    ("image", EmailImageBlock()),
    ("divider", EmailDividerBlock()),
    ("spacer", EmailSpacerBlock()),
]

#: MJML components the section's (column-level) content compiles to.
EMAIL_SECTION_CHILDREN = frozenset(
    {
        "mj-text",
        "mj-button",
        "mj-image",
        "mj-divider",
        "mj-spacer",
    }
)


class EmailSectionBlock(EmailThemedMixin, SectionBlock):
    email_mjml_tag = "mj-section"
    email_allowed_children = EMAIL_SECTION_CHILDREN
    content = blocks.StreamBlock(EMAIL_COLUMN_BLOCKS, label=_("Content"))

    class Meta:
        abstract = False
        icon = "placeholder"
        label = _("Section")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/section.html"
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "alignment", "audience"],
        )
