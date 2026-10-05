from django.conf import settings
from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.blocks.accordion import AccordionBlock
from wagtail_daisIE.blocks.inline import HeaderBlock, InlineTextBlock
from wagtail_daisIE.blocks.spaced import LinkListBlock

from ..base_blocks import (
    AbstractLinkBlock,
    PublicThemedBlock,
    ThemedBlock,
)
from ..base_blocks.compact import DaisieStreamBlock
from ..base_blocks.markup import strip_inline_markup
from ..choicelist import ChoiceList
from ..dynamic.action_blocks import ActionBlock
from .cards import InlineCardBlock
from .link import ButtonBlock, LabelLinkBlock
from .media import ImageBlock
from .registry import menu_block_contributions, register_menu_block


SEARCH_FORM_METHOD_CHOICES = ChoiceList(
    [
        ("get", "GET"),
        ("post", "POST"),
    ],
    "SEARCH_FORM_METHOD_CHOICES",
)


class MenuLogo(ImageBlock):
    """A logo image with the same fields/design as the image block.

    Rendered inline (next to the wordmark) and sized through the media design
    ``size`` (e.g. a height class) rather than a hard-coded width.
    """

    alt = blocks.CharBlock(
        max_length=255,
        required=False,
        blank=True,
        label=_("Alternative text"),
        help_text=_(
            "Describes the logo for screen readers. Falls back to the wordmark."
        ),
    )

    class Meta:
        abstract = False
        icon = "image"
        group = _("Branding")
        collapsed = True
        template = "wagtail_daisIE/blocks/menu_logo.html"
        form_layout = blocks.BlockGroup(
            children=["image", "image_source", "image_expression", "alt"],
            settings=["design", "audience", "caption", "attribution"],
        )


class MenuBranding(AbstractLinkBlock, PublicThemedBlock):
    """Logo and/or wordmark, optionally wrapped in a single destination link."""

    logo = MenuLogo(required=False)
    logo_after = blocks.BooleanBlock(
        default=False,
        required=False,
        help_text=_("Place the logo after the wordmark"),
    )
    wordmark = InlineTextBlock(required=False)

    class Meta:
        icon = "site"
        group = _("Branding")
        collapsed = True
        template = "wagtail_daisIE/blocks/menu_branding.html"
        form_layout = blocks.BlockGroup(
            children=[
                "logo",
                "logo_after",
                "wordmark",
                "destination",
                "open_in_new_tab",
            ],
            settings=["design"],
        )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context["fallback_alt"] = strip_inline_markup(
            (value.get("wordmark") or {}).get("text", "")
        )
        return context


class MenuSearchBoxBlock(ThemedBlock):
    search_url = blocks.URLBlock(
        required=False,
        default="/search/",
    )
    search_parameter = blocks.CharBlock(
        max_length=64,
        default="query",
    )
    search_placeholder = blocks.CharBlock(
        max_length=128,
        default=_("Search"),
    )
    method = blocks.ChoiceBlock(
        choices=SEARCH_FORM_METHOD_CHOICES,
        default="get",
        required=False,
        label=_("Form method"),
    )

    class Meta:
        icon = "search"
        label = _("Search box")
        group = _("Menu items")
        collapsed = True
        label_format = "Search"
        form_layout = blocks.BlockGroup(
            children=[
                "search_url",
                "search_parameter",
                "search_placeholder",
                "method",
            ],
            settings=["design", "audience"],
        )
        template = "wagtail_daisIE/blocks/menu_search.html"
        preview_template = "wagtail_daisIE/blocks/menu_search.html"
        preview_value = {
            "search_url": "/search/",
            "search_parameter": "query",
            "search_placeholder": "Search",
            "method": "get",
        }


MENU_ITEM_BLOCKS = [
    ("link", LabelLinkBlock()),
    ("button", ButtonBlock()),
    ("search", MenuSearchBoxBlock()),
    ("inline_card", InlineCardBlock()),
    ("accordion", AccordionBlock()),
    ("link_list", LinkListBlock()),
    ("header", HeaderBlock()),
    ("text", InlineTextBlock()),
    ("action", ActionBlock()),
]

if "wagtail_daisIE.notifications" in settings.INSTALLED_APPS:
    from ..notifications.blocks import MenuNewsletterBlock

    register_menu_block("newsletter", MenuNewsletterBlock())

MENU_ITEM_BLOCKS.extend(menu_block_contributions())


class MenuItemStreamBlock(DaisieStreamBlock):
    """Top-level menu item stream used by the ``DaisyUIMenu`` snippet."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("local_blocks", MENU_ITEM_BLOCKS)
        super().__init__(*args, **kwargs)

    class Meta:
        icon = "list-ul"
        label = _("Menu items")
        group = _("Menu")
