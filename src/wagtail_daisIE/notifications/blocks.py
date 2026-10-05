"""Email/campaign blocks: reusable variables and the newsletter signup."""

from __future__ import annotations

from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.snippets.blocks import SnippetChooserBlock

from ..base_blocks import InlineMarkupBlock, ThemedBlock
from ..base_blocks.compact import DaisieStructBlock
from ..choicelist import ChoiceList


NEWSLETTER_MODE_CHOICES = ChoiceList(
    [
        ("external", _("External URL")),
        ("daisie", _("Daisie audience")),
    ],
    "NEWSLETTER_MODE_CHOICES",
)
NEWSLETTER_METHOD_CHOICES = ChoiceList(
    [
        ("post", "POST"),
        ("get", "GET"),
    ],
    "NEWSLETTER_METHOD_CHOICES",
)


class EmailVariableBlock(DaisieStructBlock):
    """A key/value pair exposed to an email as ``{{ payload.<key> }}``."""

    key = blocks.CharBlock(
        max_length=64,
        label=_("Name"),
        help_text=_("The variable name, without braces."),
    )
    value = blocks.CharBlock(
        max_length=255,
        required=False,
        help_text=_("May itself contain placeholders."),
    )

    class Meta:
        icon = "tag"
        label = _("Variable")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=["key", "value"],
            heading=_("Variable"),
        )


class NewsletterSignupBlock(ThemedBlock):
    """A DaisyUI newsletter signup form posting to the subscribe endpoint."""

    target_audience = SnippetChooserBlock(
        "wagtail_daisIE_notifications.Audience",
        required=False,
        label=_("Audience"),
        help_text=_("Manual audience that new subscribers are added to."),
    )
    heading = InlineMarkupBlock(max_length=255, required=False, blank=True)
    description = InlineMarkupBlock(max_length=255, required=False, blank=True)
    placeholder = blocks.CharBlock(max_length=128, default="Enter your email")
    button_label = InlineMarkupBlock(max_length=64, default="Subscribe")
    success_message = blocks.CharBlock(
        max_length=255,
        required=False,
        blank=True,
        default="Thanks! Please check your inbox.",
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
        try:
            context["subscribe_url"] = reverse("wagtail_daisIE_notifications:subscribe")
        except NoReverseMatch:
            context["subscribe_url"] = ""
        audience = value.get("target_audience")
        context["audience_id"] = getattr(audience, "pk", None)
        return context

    class Meta:
        icon = "mail"
        group = _("Newsletter")
        collapsed = True
        template = "wagtail_daisIE/blocks/newsletter_signup.html"
        form_layout = blocks.BlockGroup(
            children=[
                "target_audience",
                "heading",
                "description",
                "placeholder",
                "button_label",
                "success_message",
            ],
            settings=["design", "audience"],
        )


class MenuNewsletterBlock(ThemedBlock):
    """A newsletter signup placed in a menu item stream."""

    mode = blocks.ChoiceBlock(
        choices=NEWSLETTER_MODE_CHOICES,
        default="external",
        help_text=_("Post to an external service or to a Daisie audience."),
    )
    action = blocks.URLBlock(
        required=False,
        blank=True,
        label=_("Form action URL"),
        help_text=_("Used when the mode is an external URL."),
    )
    target_audience = SnippetChooserBlock(
        "wagtail_daisIE_notifications.Audience",
        required=False,
        label=_("Audience"),
        help_text=_("Used when the mode is a Daisie audience."),
    )
    method = blocks.ChoiceBlock(
        choices=NEWSLETTER_METHOD_CHOICES,
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
    )
    button_label = InlineMarkupBlock(
        max_length=64,
        default=_("Subscribe"),
    )
    success_message = blocks.CharBlock(
        max_length=255,
        required=False,
        blank=True,
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
        context["newsletter_action"] = value.get("action") or ""
        context["audience_id"] = None
        if (value.get("mode") or "external") == "daisie":
            try:
                context["newsletter_action"] = reverse(
                    "wagtail_daisIE_notifications:subscribe"
                )
            except NoReverseMatch:
                context["newsletter_action"] = ""
            context["audience_id"] = getattr(value.get("target_audience"), "pk", None)
        return context

    class Meta:
        icon = "mail"
        label = _("Newsletter")
        group = _("Menu items")
        collapsed = True
        label_format = "Newsletter"
        form_layout = blocks.BlockGroup(
            children=[
                "mode",
                "action",
                "target_audience",
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
            "mode": "external",
            "action": "/subscribe/",
            "method": "post",
            "placeholder": "Enter your email",
            "button_label": "Subscribe",
        }
