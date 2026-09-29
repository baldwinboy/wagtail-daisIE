"""Structural MJML blocks.

MJML only permits ``mj-column`` inside ``mj-section``/``mj-group`` and leaf
components inside ``mj-column``. A section defaults to a single implicit column
for the common case, but editors can also place explicit **Column** and
**Group** blocks when they need multi-column layouts. **Wrapper** and **Hero**
are body-level containers.
"""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ...base_blocks.design import ThemedBlock
from ...blocks.section import SectionBlock
from .base import EmailThemedMixin
from .design import (
    EmailImageDesignBlock,
    EmailImageSpacedDesignBlock,
    EmailSolidDesignBlock,
)
from .leaves import (
    EmailAccordionBlock,
    EmailButtonBlock,
    EmailCarouselBlock,
    EmailDividerBlock,
    EmailHeaderBlock,
    EmailImageBlock,
    EmailLinkBlock,
    EmailNavbarBlock,
    EmailRichTextBlock,
    EmailSocialBlock,
    EmailSpacerBlock,
    EmailTableBlock,
    EmailTextBlock,
)


#: Leaf components that may be placed inside an ``mj-column``.
EMAIL_COLUMN_BLOCKS = [
    ("header", EmailHeaderBlock()),
    ("text", EmailTextBlock()),
    ("rich_text", EmailRichTextBlock()),
    ("button", EmailButtonBlock()),
    ("link", EmailLinkBlock()),
    ("image", EmailImageBlock()),
    ("divider", EmailDividerBlock()),
    ("spacer", EmailSpacerBlock()),
    ("accordion", EmailAccordionBlock()),
    ("carousel", EmailCarouselBlock()),
    ("navbar", EmailNavbarBlock()),
    ("social", EmailSocialBlock()),
    ("table", EmailTableBlock()),
]


class EmailColumnBlock(EmailThemedMixin, ThemedBlock):
    email_mjml_tag = "mj-column"
    design = EmailSolidDesignBlock()
    content = blocks.StreamBlock(EMAIL_COLUMN_BLOCKS, label=_("Column content"))

    class Meta:
        abstract = False
        icon = "placeholder"
        label = _("Column")
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/column.html"
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "audience"],
        )


class EmailGroupBlock(EmailThemedMixin, ThemedBlock):
    email_mjml_tag = "mj-group"
    design = EmailSolidDesignBlock()
    columns = blocks.StreamBlock([("column", EmailColumnBlock())])

    class Meta:
        abstract = False
        icon = "placeholder"
        label = _("Group")
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/group.html"
        form_layout = blocks.BlockGroup(
            children=["columns"],
            settings=["design", "audience"],
        )


#: Components that may be a direct child of ``mj-column`` (validation helper).
EMAIL_SECTION_CHILDREN = frozenset(
    {
        "mj-text",
        "mj-button",
        "mj-image",
        "mj-divider",
        "mj-spacer",
        "mj-accordion",
        "mj-carousel",
        "mj-navbar",
        "mj-social",
        "mj-table",
    }
)


class EmailSectionBlock(EmailThemedMixin, SectionBlock):
    email_mjml_tag = "mj-section"
    email_allowed_children = EMAIL_SECTION_CHILDREN
    design = EmailImageSpacedDesignBlock()
    content = blocks.StreamBlock(
        [
            ("column", EmailColumnBlock()),
            ("group", EmailGroupBlock()),
            *EMAIL_COLUMN_BLOCKS,
        ],
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
        context["has_columns"] = any(
            getattr(child, "block_type", None) in ("column", "group")
            for child in (value.get("content") or [])
        )
        return context

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


class EmailHeroBlock(EmailThemedMixin, ThemedBlock):
    email_mjml_tag = "mj-hero"
    design = EmailImageDesignBlock()
    height = blocks.CharBlock(required=False, blank=True, help_text=_("e.g. 400px"))
    content = blocks.StreamBlock(EMAIL_COLUMN_BLOCKS, label=_("Hero content"))

    class Meta:
        abstract = False
        icon = "image"
        label = _("Hero")
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/hero.html"
        form_layout = blocks.BlockGroup(
            children=["height", "content"],
            settings=["design", "audience"],
        )


class EmailWrapperBlock(EmailThemedMixin, ThemedBlock):
    email_mjml_tag = "mj-wrapper"
    design = EmailImageDesignBlock()
    content = blocks.StreamBlock(
        [
            ("section", EmailSectionBlock()),
            ("hero", EmailHeroBlock()),
        ],
    )

    class Meta:
        abstract = False
        icon = "placeholder"
        label = _("Wrapper")
        group = _("Layout")
        collapsed = True
        template = "wagtail_daisIE/emails/blocks/wrapper.html"
        form_layout = blocks.BlockGroup(
            children=["content"],
            settings=["design", "audience"],
        )
