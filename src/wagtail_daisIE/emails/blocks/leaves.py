"""Leaf MJML blocks — components that live inside an ``mj-column``.

Each block reuses the matching web block (fields and design composites) and
only swaps the template + MJML tag. A fresh ``Meta`` is declared because
Wagtail strips the ``Meta`` attribute from blocks; options such as ``icon``,
``group`` and ``form_layout`` are inherited through the block's ``_meta_class``.
"""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ...base_blocks.design import ThemedBlock
from ...blocks.blockquote import BlockQuote
from ...blocks.inline import (
    CopyrightBlock,
    HeaderBlock,
    InlineRichTextBlock,
    InlineTextBlock,
)
from ...blocks.link import ButtonBlock, InlineLinkBlock
from ...blocks.media import ImageBlock
from .base import EmailThemedMixin


class EmailHeaderBlock(EmailThemedMixin, HeaderBlock):
    email_mjml_tag = "mj-text"

    class Meta:
        template = "wagtail_daisIE/emails/blocks/text.html"


class EmailTextBlock(EmailThemedMixin, InlineTextBlock):
    email_mjml_tag = "mj-text"

    class Meta:
        template = "wagtail_daisIE/emails/blocks/text.html"


class EmailRichTextBlock(EmailThemedMixin, InlineRichTextBlock):
    email_mjml_tag = "mj-text"

    class Meta:
        template = "wagtail_daisIE/emails/blocks/rich_text.html"


class EmailCopyrightBlock(EmailThemedMixin, CopyrightBlock):
    email_mjml_tag = "mj-text"

    class Meta:
        template = "wagtail_daisIE/emails/blocks/text.html"


class EmailBlockquoteBlock(EmailThemedMixin, BlockQuote):
    email_mjml_tag = "mj-text"

    class Meta:
        template = "wagtail_daisIE/emails/blocks/blockquote.html"


class EmailButtonBlock(EmailThemedMixin, ButtonBlock):
    email_mjml_tag = "mj-button"

    class Meta:
        template = "wagtail_daisIE/emails/blocks/button.html"


class EmailLinkBlock(EmailThemedMixin, InlineLinkBlock):
    email_mjml_tag = "mj-text"

    class Meta:
        template = "wagtail_daisIE/emails/blocks/link.html"


class EmailImageBlock(EmailThemedMixin, ImageBlock):
    email_mjml_tag = "mj-image"

    class Meta:
        template = "wagtail_daisIE/emails/blocks/image.html"


class EmailDividerBlock(EmailThemedMixin, ThemedBlock):
    email_mjml_tag = "mj-divider"

    class Meta:
        abstract = False
        icon = "horizontalrule"
        label = _("Divider")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/divider.html"
        form_layout = blocks.BlockGroup(
            children=[],
            settings=["design", "audience"],
        )


class EmailSpacerBlock(EmailThemedMixin, ThemedBlock):
    email_mjml_tag = "mj-spacer"

    class Meta:
        abstract = False
        icon = "plus"
        label = _("Spacer")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/spacer.html"
        form_layout = blocks.BlockGroup(
            children=[],
            settings=["design", "audience"],
        )


class EmailRawBlock(blocks.StructBlock):
    """Inline raw HTML/MJML, inserted through an ``mj-raw`` ending tag."""

    html = blocks.RawHTMLBlock(label=_("HTML"))

    class Meta:
        icon = "code"
        label = _("Raw HTML")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/raw.html"
        form_layout = blocks.BlockGroup(children=["html"], settings=[])
