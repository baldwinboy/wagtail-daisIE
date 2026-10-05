"""Leaf MJML blocks — components that live inside an ``mj-column``.

Each block reuses the matching web block (fields and design composites) and
only swaps the template + MJML tag. A fresh ``Meta`` is declared because
Wagtail strips the ``Meta`` attribute from blocks; options such as ``icon``,
``group`` and ``form_layout`` are inherited through the block's ``_meta_class``.
"""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.images.blocks import ImageBlock as WagtailImageBlock

from ...base_blocks.compact import DaisieStructBlock
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
from ...choicelist import ChoiceList
from .base import EmailThemedMixin
from .design import (
    EmailNavbarDesignBlock,
    EmailSolidButtonDesignBlock,
    EmailSolidDesignBlock,
    EmailSolidMediaDesignBlock,
    EmailSolidTypographyDesignBlock,
)


SOCIAL_NETWORK_CHOICES = ChoiceList(
    [
        ("facebook", "Facebook"),
        ("twitter", "Twitter / X"),
        ("instagram", "Instagram"),
        ("linkedin", "LinkedIn"),
        ("github", "GitHub"),
        ("youtube", "YouTube"),
        ("web", "Website"),
        ("email", "Email"),
    ],
    "SOCIAL_NETWORK_CHOICES",
)


class EmailHeaderBlock(EmailThemedMixin, HeaderBlock):
    email_mjml_tag = "mj-text"
    design = EmailSolidTypographyDesignBlock()

    class Meta:
        template = "wagtail_daisIE/emails/blocks/text.html"


class EmailTextBlock(EmailThemedMixin, InlineTextBlock):
    email_mjml_tag = "mj-text"
    design = EmailSolidTypographyDesignBlock()

    class Meta:
        template = "wagtail_daisIE/emails/blocks/text.html"


class EmailRichTextBlock(EmailThemedMixin, InlineRichTextBlock):
    email_mjml_tag = "mj-text"
    design = EmailSolidTypographyDesignBlock()

    class Meta:
        template = "wagtail_daisIE/emails/blocks/rich_text.html"


class EmailCopyrightBlock(EmailThemedMixin, CopyrightBlock):
    email_mjml_tag = "mj-text"
    design = EmailSolidTypographyDesignBlock()

    class Meta:
        template = "wagtail_daisIE/emails/blocks/text.html"


class EmailBlockquoteBlock(EmailThemedMixin, BlockQuote):
    email_mjml_tag = "mj-text"
    design = EmailSolidTypographyDesignBlock()

    class Meta:
        template = "wagtail_daisIE/emails/blocks/blockquote.html"


class EmailButtonBlock(EmailThemedMixin, ButtonBlock):
    email_mjml_tag = "mj-button"
    design = EmailSolidButtonDesignBlock()

    class Meta:
        template = "wagtail_daisIE/emails/blocks/button.html"


class EmailLinkBlock(EmailThemedMixin, InlineLinkBlock):
    email_mjml_tag = "mj-text"
    design = EmailSolidTypographyDesignBlock()

    class Meta:
        template = "wagtail_daisIE/emails/blocks/link.html"


class EmailImageBlock(EmailThemedMixin, ImageBlock):
    email_mjml_tag = "mj-image"
    design = EmailSolidMediaDesignBlock()

    class Meta:
        template = "wagtail_daisIE/emails/blocks/image.html"


class EmailDividerBlock(EmailThemedMixin, ThemedBlock):
    email_mjml_tag = "mj-divider"
    design = EmailSolidDesignBlock()

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
    design = EmailSolidDesignBlock()

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


class EmailRawBlock(DaisieStructBlock):
    """Inline raw HTML/MJML, inserted through an ``mj-raw`` ending tag."""

    html = blocks.RawHTMLBlock()

    class Meta:
        icon = "code"
        label = _("Raw HTML")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/raw.html"
        form_layout = blocks.BlockGroup(children=["html"], settings=[])


class EmailAccordionBlock(EmailThemedMixin, ThemedBlock):
    """``mj-accordion`` with title/text elements."""

    email_mjml_tag = "mj-accordion"
    design = EmailSolidDesignBlock()

    items = blocks.ListBlock(
        DaisieStructBlock(
            [
                ("title", blocks.CharBlock(max_length=255, label=_("Title"))),
                ("text", blocks.RichTextBlock(label=_("Content"))),
            ],
            label=_("Item"),
        ),
    )

    class Meta:
        abstract = False
        icon = "collapse-down"
        label = _("Accordion")
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/accordion.html"
        form_layout = blocks.BlockGroup(
            children=["items"],
            settings=["design", "audience"],
        )


class EmailCarouselBlock(EmailThemedMixin, ThemedBlock):
    """``mj-carousel`` of images."""

    email_mjml_tag = "mj-carousel"
    design = EmailSolidDesignBlock()

    images = blocks.ListBlock(
        DaisieStructBlock(
            [
                ("image", WagtailImageBlock(label=_("Image"))),
                (
                    "href",
                    blocks.URLBlock(required=False, blank=True, label=_("Link")),
                ),
            ],
            label=_("Slide"),
        ),
        label=_("Slides"),
    )

    class Meta:
        abstract = False
        icon = "image"
        label = _("Carousel")
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/carousel.html"
        form_layout = blocks.BlockGroup(
            children=["images"],
            settings=["design", "audience"],
        )


class EmailNavbarBlock(EmailThemedMixin, ThemedBlock):
    """``mj-navbar`` of links."""

    email_mjml_tag = "mj-navbar"
    design = EmailNavbarDesignBlock()

    links = blocks.ListBlock(
        DaisieStructBlock(
            [
                ("text", blocks.CharBlock(max_length=255, label=_("Text"))),
                ("href", blocks.URLBlock(label=_("Link"))),
            ],
            label=_("Link"),
        ),
    )

    class Meta:
        abstract = False
        icon = "list-ul"
        label = _("Navbar")
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/navbar.html"
        form_layout = blocks.BlockGroup(
            children=["links"],
            settings=["design", "audience"],
        )


class EmailSocialBlock(EmailThemedMixin, ThemedBlock):
    """``mj-social`` of named network elements (icons supplied by MJML)."""

    email_mjml_tag = "mj-social"
    design = EmailSolidDesignBlock()

    elements = blocks.ListBlock(
        DaisieStructBlock(
            [
                (
                    "name",
                    blocks.ChoiceBlock(
                        choices=SOCIAL_NETWORK_CHOICES,
                        label=_("Network"),
                    ),
                ),
                ("href", blocks.URLBlock(label=_("Link"))),
            ],
            label=_("Element"),
        ),
    )

    class Meta:
        abstract = False
        icon = "site"
        label = _("Social")
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/social.html"
        form_layout = blocks.BlockGroup(
            children=["elements"],
            settings=["design", "audience"],
        )


class EmailTableBlock(EmailThemedMixin, ThemedBlock):
    """``mj-table`` with raw table markup."""

    email_mjml_tag = "mj-table"
    design = EmailSolidDesignBlock()

    html = blocks.RawHTMLBlock(label=_("Table HTML"))

    class Meta:
        abstract = False
        icon = "table"
        label = _("Table")
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/table.html"
        form_layout = blocks.BlockGroup(
            children=["html"],
            settings=["design", "audience"],
        )
