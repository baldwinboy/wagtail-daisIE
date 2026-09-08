import logging

from django import forms
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.admin.telepath import register
from wagtail.blocks.struct_block import StructBlockAdapter


logger = logging.getLogger(__name__)


def get_audience_choices():
    return [
        (key, config["label"])
        for key, config in getattr(
            settings, "WAGTAIL_DAISIE_AUDIENCE_RULES", {}
        ).items()
    ]


def evaluate_audience(audience_keys, request):
    """Evaluate a list of audience keys against the configured rules.

    Rules are looked up in ``WAGTAIL_DAISIE_AUDIENCE_RULES`` as dotted paths to
    callables that accept ``request`` and return a bool. The audience is
    considered allowed when **any** of the selected rules passes.

    Missing rules are ignored, and without a request (or with an empty audience)
    the content is always considered allowed so that previews and email
    rendering never hide content inadvertently.
    """
    if not audience_keys or request is None:
        return True
    rules = getattr(settings, "WAGTAIL_DAISIE_AUDIENCE_RULES", {})
    for key in audience_keys:
        config = rules.get(key)
        rule = (config or {}).get("rule")
        if not rule:
            continue
        try:
            rule_callable = import_string(rule)
        except ImportError as exc:
            logger.warning("Could not resolve audience rule %r: %s", rule, exc)
            continue
        try:
            if rule_callable(request):
                return True
        except Exception:
            logger.exception("Audience rule %r raised while evaluating", rule)
    return False


class AudienceBlock(blocks.StructBlock):
    """
    Restrict a block to a named audience.

    Audiences are declared in project settings and evaluated at render time.
    """

    audience = blocks.MultipleChoiceBlock(
        choices=get_audience_choices,
        default=[],
        required=False,
        label=_("Audience"),
        help_text=_(
            "Select the audiences that can see this content."
            "Leave empty to show to all audiences."
        ),
    )

    class Meta:
        icon = "group"
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=["audience"],
            heading=_("Limit content to audiences"),
        )


class AudienceBlockAdapter(StructBlockAdapter):
    js_constructor = "wagtail_daisIE.base_blocks.AudienceBlock"

    @cached_property
    def media(self):
        structblock_media = super().media
        return forms.Media(
            js=[
                *structblock_media._js,
                "wagtail_daisIE/js/audience_block.js",
            ],
            css=structblock_media._css,
        )


register(AudienceBlockAdapter(), AudienceBlock)
