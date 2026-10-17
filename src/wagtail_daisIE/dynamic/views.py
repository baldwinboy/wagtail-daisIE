"""Admin endpoints backing dynamic context widgets."""

from __future__ import annotations

import re

from urllib.parse import urlencode

from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import escape, format_html
from django.views.decorators.http import require_GET, require_POST
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh

from ..icons import render_icon, validate_icon
from ..icons.value import IconValueError
from .action_blocks import ALERT_TAGS
from .actions import run_action
from .feeds import render_feed
from .registry import get_context_models, resolve_model
from .resolvers import model_options


#: Confirmation level keyword -> Django messages level constant.
_MESSAGE_LEVELS = {
    "success": messages.SUCCESS,
    "warning": messages.WARNING,
    "error": messages.ERROR,
    "info": messages.INFO,
}


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


@require_GET
def binding_results(request):
    """Return an HTML fragment of instance options for a configured model.

    Backs the ``w-swap`` search in the context-binding block. The request
    carries ``model`` (the configured model path), the search ``q``, a ``limit``,
    ``target`` (the hidden input the chosen value is written to) and ``panel``
    (the results container that is swapped). With ``selected`` it returns the
    chosen item's display fragment; with ``clear`` it returns an empty body.
    """
    user = getattr(request, "user", None)
    if not (user and user.is_staff):
        raise Http404

    model = resolve_model(request.GET.get("model", ""))
    if model is None or model not in _configured_models():
        raise Http404

    target = request.GET.get("target", "")
    panel = request.GET.get("panel", "")
    if not (_TARGET_SELECTOR.fullmatch(target) and _TARGET_SELECTOR.fullmatch(panel)):
        return HttpResponseBadRequest("Invalid selector")

    base = {"model": request.GET.get("model", ""), "target": target, "panel": panel}
    endpoint = reverse("wagtail_daisIE:binding_results")
    clear_url = endpoint + "?" + urlencode({**base, "clear": "1"})

    def render_selected(obj):
        return render(
            request,
            "wagtail_daisIE/admin/binding_results.html",
            {
                "selected": {"id": obj.pk, "text": str(obj)},
                "target": target,
                "panel": panel,
                "clear_url": clear_url,
            },
        )

    if request.GET.get("clear"):
        return HttpResponse("")

    selected = (request.GET.get("selected") or "").strip()
    if selected:
        try:
            obj = model._default_manager.get(pk=selected)
        except (model.DoesNotExist, TypeError, ValueError):
            raise Http404 from None
        return render_selected(obj)

    if not request.GET.get("q", "").strip():
        current = (request.GET.get("current") or "").strip()
        if not current:
            return HttpResponse("")
        try:
            obj = model._default_manager.get(pk=current)
        except (model.DoesNotExist, TypeError, ValueError):
            return HttpResponse("")
        return render_selected(obj)

    try:
        limit = int(request.GET.get("limit", 50) or 50)
    except (TypeError, ValueError):
        limit = 50
    limit = max(1, min(limit, 500))

    results = model_options(model, query=request.GET.get("q", ""), limit=limit)
    for item in results:
        item["selected_url"] = (
            endpoint + "?" + urlencode({**base, "selected": item["id"]})
        )

    return render(
        request,
        "wagtail_daisIE/admin/binding_results.html",
        {
            "results": results,
            "target": target,
            "panel": panel,
            "clear_url": clear_url,
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
            text, icon, tags, _level = _confirmation_values(request)
            fragment = render_to_string(
                "wagtail_daisIE/blocks/data/action_form_status.html",
                {
                    "message_text": text,
                    "message_icon": icon,
                    "message_tags": " ".join(tags),
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

    try:
        offset = int(request.GET.get("offset", 0) or 0)
    except (TypeError, ValueError):
        offset = 0
    raw_limit = request.GET.get("limit")
    if raw_limit in (None, ""):
        limit = None
    else:
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            limit = None

    page = None
    raw_page = request.GET.get("page")
    if raw_page:
        from wagtail.models import Page

        page = Page.objects.filter(pk=raw_page).first()
        if page is not None:
            page = page.specific

    data = render_feed(feed, request, offset=offset, limit=limit, page=page)
    data.update(
        {
            "block_id": request.GET.get("block", ""),
            "empty_message": feed.empty_message,
            "feed_url": reverse("wagtail_daisIE_dynamic:feed_items", args=[feed.pk]),
        }
    )
    return render(request, "wagtail_daisIE/blocks/data/feed_body.html", data)
