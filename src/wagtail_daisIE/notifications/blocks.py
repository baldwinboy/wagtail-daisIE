"""Email/campaign blocks: reusable variables and the newsletter signup."""

from __future__ import annotations

from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.snippets.blocks import SnippetChooserBlock

from ..base_blocks import ThemedBlock


class EmailVariableBlock(blocks.StructBlock):
    """A key/value pair exposed to an email as ``{{ payload.<key> }}``."""

    key = blocks.CharBlock(
        max_length=64,
        label=_("Name"),
        help_text=_("The variable name, without braces."),
    )
    value = blocks.CharBlock(
        max_length=255,
        required=False,
        label=_("Value"),
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
        "wagtail_daisIE.Audience",
        required=False,
        label=_("Audience"),
        help_text=_("Manual audience that new subscribers are added to."),
    )
    heading = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Heading")
    )
    description = blocks.CharBlock(
        max_length=255, required=False, blank=True, label=_("Description")
    )
    placeholder = blocks.CharBlock(
        max_length=128, default="Enter your email", label=_("Placeholder")
    )
    button_label = blocks.CharBlock(
        max_length=64, default="Subscribe", label=_("Button label")
    )
    success_message = blocks.CharBlock(
        max_length=255,
        required=False,
        blank=True,
        default="Thanks! Please check your inbox.",
        label=_("Success message"),
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
