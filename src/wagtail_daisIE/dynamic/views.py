"""Admin endpoints backing dynamic context widgets."""

from __future__ import annotations

import logging
import re

from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import escape, format_html
from django.views.decorators.http import require_GET, require_POST
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh
from wagtail.admin.auth import require_admin_access

from ..icons import render_icon, validate_icon
from ..icons.value import IconValueError
from .action_blocks import ALERT_TAGS
from .actions import run_action
from .feeds import (
    decode_layout_override,
    encode_layout_override,
    render_feed,
)
from .registry import get_context_models, resolve_model
from .resolvers import model_options


logger = logging.getLogger(__name__)


#: Confirmation level keyword -> Django messages level constant.
_MESSAGE_LEVELS = {
    "success": messages.SUCCESS,
    "warning": messages.WARNING,
    "error": messages.ERROR,
    "info": messages.INFO,
}

#: Django messages level constant -> alert class suffix.
_MESSAGE_LEVEL_TAGS = {level: name for name, level in _MESSAGE_LEVELS.items()}


def _safe_icon_html(icon):
    """Render a validated icon value to safe HTML, or an empty string."""
    if not icon:
        return ""
    try:
        validate_icon(icon)
    except IconValueError:
        return ""
    return render_icon(icon)


def _confirmation_values(request):
    """Return the (untrusted) confirmation fields submitted with an action."""
    text = (request.POST.get("daisie_message") or "").strip()
    icon = (request.POST.get("daisie_message_icon") or "").strip()
    tags = [
        tag
        for tag in (request.POST.get("daisie_message_tags") or "").split()
        if tag in ALERT_TAGS
    ]
    level = _MESSAGE_LEVELS.get(
        (request.POST.get("daisie_message_level") or "").strip(), messages.INFO
    )
    return text, icon, tags, level


def _add_confirmation(request):
    """Add the action block's confirmation to the messages framework.

    Values arrive as hidden form fields, so they are treated as untrusted:
    the text is escaped, the icon is validated, and only allowlisted alert
    classes are accepted.
    """
    text, icon, tags, level = _confirmation_values(request)
    if not text:
        return
    safe = format_html(
        '<span aria-hidden="true">{}</span>{}',
        _safe_icon_html(icon),
        escape(text),
    )
    messages.add_message(request, level, safe, extra_tags=" ".join(tags))


#: ``target``/``panel`` must be simple id selectors, e.g. ``#form_fields-0-object_id``.
_TARGET_SELECTOR = re.compile(r"#[A-Za-z0-9_-]+")


def _configured_models():
    """Return the set of models configured as context models."""
    models = set()
    for config in get_context_models().values():
        model = config.model
        if model is not None:
            models.add(model)
    return models


def _config_for_model(model):
    for config in get_context_models().values():
        if config.model is model:
            return config
    return None


@require_GET
def binding_results(request):
    """Return an HTML fragment of instance options for a configured model."""
    query = (request.GET.get("q") or "").strip()
    if len(query) < 2:
        return HttpResponse("")

    return _binding_results(request)


@require_GET
@require_admin_access
def _binding_results(request):
    """Authenticated search path for context binding instances."""
    model = resolve_model(request.GET.get("model", ""))
    if model is None or model not in _configured_models():
        raise Http404

    target = request.GET.get("target", "")
    panel = request.GET.get("panel", "")
    if not (_TARGET_SELECTOR.fullmatch(target) and _TARGET_SELECTOR.fullmatch(panel)):
        return HttpResponseBadRequest("Invalid selector")

    config = _config_for_model(model)

    query = (request.GET.get("q") or "").strip()

    try:
        limit = int(request.GET.get("limit", 20) or 20)
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 20))

    results = model_options(config, request=request, query=query, limit=limit)

    return render(
        request,
        "wagtail_daisIE/admin/binding_results.html",
        {
            "results": results,
            "target": target,
            "panel": panel,
        },
    )


@require_POST
def action(request, action_key):
    """Run a configured action and follow its response.

    htmx requests get a granular response: a redirect becomes ``HX-Redirect``,
    ``behaviour=reload`` refreshes the page, and the default returns the
    confirmation as an inline alert fragment. Plain requests keep the existing
    messages + redirect behaviour.
    """
    response = run_action(request, action_key)
    if getattr(request, "htmx", False):
        behaviour = (request.POST.get("daisie_behaviour") or "inline").strip()
        if behaviour == "inline":
            # Update the status area in place; ignore any handler redirect so
            # "save on change" does not navigate away.
            text, icon, tags, level = _confirmation_values(request)
            fragment = render_to_string(
                "wagtail_daisIE/blocks/data/action_form_status.html",
                {
                    "message_text": text,
                    "message_icon": icon,
                    "message_tags": " ".join(tags),
                    "message_level": _MESSAGE_LEVEL_TAGS.get(level, "info"),
                },
                request=request,
            )
            return HttpResponse(fragment)
        redirect_response = response is not None and 300 <= response.status_code < 400
        if redirect_response:
            return HttpResponseClientRedirect(response.get("Location") or "/")
        return HttpResponseClientRefresh()
    _add_confirmation(request)
    if response is None:
        return redirect(request.META.get("HTTP_REFERER") or "/")
    return response


@require_GET
def feed_items(request, pk):
    """Render a feed body fragment for htmx filter, layout and load-more swaps."""
    from ..feeds.models import Feed

    try:
        feed = Feed.objects.get(pk=pk)
    except Feed.DoesNotExist as exc:
        raise Http404 from exc

    source_page = None
    raw_source_page = request.GET.get("source_page")
    if raw_source_page:
        from wagtail.models import Page

        try:
            page_pk = int(raw_source_page)
            if not (0 < page_pk < 2**31):
                raise ValueError
            source_page = Page.objects.filter(pk=page_pk).first()
            if source_page is not None:
                source_page = source_page.specific
        except (TypeError, ValueError, OverflowError, Page.DoesNotExist):
            logger.warning(
                "Ignoring invalid feed source_page parameter %r", raw_source_page
            )

    layout_token = request.GET.get("layout_token", "")
    override = decode_layout_override(layout_token)
    layout_token = encode_layout_override(override) if override else ""

    data = render_feed(
        feed,
        request,
        source_page=source_page,
        override=override,
        layout_token=layout_token,
    )
    data.update(
        {
            "block_id": request.GET.get("block", ""),
            "empty_message": feed.empty_message,
            "feed_url": reverse("wagtail_daisIE_dynamic:feed_items", args=[feed.pk]),
        }
    )
    template = (
        "wagtail_daisIE/blocks/data/feed_items.html"
        if request.GET.get("fragment") == "items"
        else "wagtail_daisIE/blocks/data/feed_body.html"
    )
    return render(request, template, data)
