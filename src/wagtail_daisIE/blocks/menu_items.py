from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.images.blocks import ImageBlock as WagtailImageBlock

from wagtail_daisIE.blocks.accordion import AccordionBlock
from wagtail_daisIE.blocks.inline import HeaderBlock, InlineTextBlock
from wagtail_daisIE.blocks.spaced import LinkListBlock

from ..base_blocks import (
    AbstractLinkBlock,
    PublicThemedBlock,
    PublicThemedMediaBlock,
    ThemedBlock,
)
from .cards import InlineCardBlock
from .link import ButtonBlock, LabelLinkBlock


class MenuLogo(PublicThemedMediaBlock):
    image = WagtailImageBlock(
        help_text=_("Logo image shown next to the wordmark."),
    )
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
        icon = "image"
        group = _("Branding")
        collapsed = True
        template = "wagtail_daisIE/blocks/menu_logo.html"
        form_layout = blocks.BlockGroup(
            children=["image", "alt"],
            settings=["design"],
        )


class MenuBranding(AbstractLinkBlock, PublicThemedBlock):
    """Logo and/or wordmark, optionally wrapped in a single destination link."""

    logo = MenuLogo(required=False)
    logo_after = blocks.BooleanBlock(
        default=False,
        label=_("Logo after"),
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
        context["fallback_alt"] = (value.get("wordmark") or {}).get("text", "")
        return context


class MenuSearchBoxBlock(ThemedBlock):
    search_url = blocks.URLBlock(
        required=False,
        default="/search/",
        label=_("Search URL"),
    )
    search_parameter = blocks.CharBlock(
        max_length=64,
        default="query",
        label=_("Search parameter"),
    )
    search_placeholder = blocks.CharBlock(
        max_length=128,
        default=_("Search"),
        label=_("Search placeholder"),
    )
    method = blocks.ChoiceBlock(
        choices=[("get", "GET"), ("post", "POST")],
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


class MenuNewsletterBlock(ThemedBlock):
    action = blocks.URLBlock(
        required=False,
        blank=True,
        label=_("Form action URL"),
    )
    method = blocks.ChoiceBlock(
        choices=[("post", "POST"), ("get", "GET")],
        default="post",
        required=False,
        label=_("Form method"),
    )
    email_field = blocks.CharBlock(
        max_length=64,
        default="email",
        label=_("Email field name"),
    )
    placeholder = blocks.CharBlock(
        max_length=128,
        default=_("Enter your email"),
        label=_("Placeholder"),
    )
    button_label = blocks.CharBlock(
        max_length=64,
        default=_("Subscribe"),
        label=_("Button label"),
    )
    success_message = blocks.CharBlock(
        max_length=255,
        required=False,
        blank=True,
        label=_("Success message"),
    )

    class Meta:
        icon = "mail"
        label = _("Newsletter")
        group = _("Menu items")
        collapsed = True
        label_format = "Newsletter"
        form_layout = blocks.BlockGroup(
            children=[
                "action",
                "method",
                "email_field",
                "placeholder",
                "button_label",
                "success_message",
            ],
            settings=["design", "audience"],
        )
        template = "wagtail_daisIE/blocks/menu_newsletter.html"
        preview_template = "wagtail_daisIE/blocks/menu_newsletter.html"
        preview_value = {
            "action": "/subscribe/",
            "method": "post",
            "placeholder": "Enter your email",
            "button_label": "Subscribe",
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
    ("newsletter", MenuNewsletterBlock()),
]


class MenuItemStreamBlock(blocks.StreamBlock):
    """Top-level menu item stream used by the ``DaisyUIMenu`` snippet."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("local_blocks", MENU_ITEM_BLOCKS)
        super().__init__(*args, **kwargs)

    class Meta:
        icon = "list-ul"
        label = _("Menu items")
        group = _("Menu")
