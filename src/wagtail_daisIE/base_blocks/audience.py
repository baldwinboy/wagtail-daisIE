import logging

from django import forms
from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
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


def get_audience_rule(key):
    """Return the raw config for an audience rule key."""
    rules = getattr(settings, "WAGTAIL_DAISIE_AUDIENCE_RULES", {})
    return rules.get(key) or {}


def get_audience_rule_choices():
    """Choices for selecting a configured audience rule."""
    return [
        (key, config.get("label", key))
        for key, config in getattr(
            settings, "WAGTAIL_DAISIE_AUDIENCE_RULES", {}
        ).items()
    ]


def resolve_audience_queryset(key):
    """Return the User queryset for a rule key's optional ``queryset``.

    Rules are ``request``-based; campaigns need a way to select users without a
    request, so a rule may additionally declare ``"queryset":
    "myapp.audience.subscribers"`` (or a callable) returning a User queryset.
    Returns ``None`` when the rule has no queryset.
    """
    rule = get_audience_rule(key)
    target = rule.get("queryset")
    if not target:
        return None
    if callable(target):
        return target()
    try:
        factory = import_string(target)
    except ImportError as exc:
        logger.warning("Could not resolve audience queryset %r: %s", target, exc)
        return None
    return factory()


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
        if callable(rule):
            rule_callable = rule
        else:
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


class PageAudienceMixin:
    """Page-level audience gating.

    Composed by ``StyledPageMixin`` (and form pages). Concrete classes supply
    the ``audience`` StreamField and the ``audience_denied``/``audience_denied_page``
    fields.
    """

    audience_denied = "403"

    def get_audience_keys(self):
        stream = getattr(self, "audience", None)
        first = stream[0].value if stream else None
        if not first:
            return []
        return list(first.get("audience") or [])

    def page_audience_allowed(self, request):
        return evaluate_audience(self.get_audience_keys(), request)

    def audience_denied_response(self, request):
        if self.audience_denied == "redirect" and getattr(
            self, "audience_denied_page_id", None
        ):
            return redirect(self.audience_denied_page.url)
        if self.audience_denied == "404":
            raise Http404
        from ..errors.handlers import render_error_page

        return render_error_page(request, 403)

    def serve(self, request, *args, **kwargs):
        if not self.page_audience_allowed(request):
            return self.audience_denied_response(request)
        return super().serve(request, *args, **kwargs)
