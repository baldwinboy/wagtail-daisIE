"""Admin endpoints backing dynamic context widgets."""

from __future__ import annotations

from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.utils.html import escape, format_html
from django.views.decorators.http import require_GET, require_POST

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


def _add_confirmation(request):
    """Add the action block's confirmation to the messages framework.

    Values arrive as hidden form fields, so they are treated as untrusted:
    the text is escaped, the icon is validated, and only allowlisted alert
    classes are accepted.
    """
    text = (request.POST.get("daisie_message") or "").strip()
    if not text:
        return
    tags = [
        tag
        for tag in (request.POST.get("daisie_message_tags") or "").split()
        if tag in ALERT_TAGS
    ]
    level = _MESSAGE_LEVELS.get(
        (request.POST.get("daisie_message_level") or "").strip(), messages.INFO
    )
    safe = format_html(
        '<span aria-hidden="true">{}</span>{}',
        _safe_icon_html(request.POST.get("daisie_message_icon")),
        escape(text),
    )
    messages.add_message(request, level, safe, extra_tags=" ".join(tags))


def _allowed_labels():
    labels = set()
    for config in get_context_models().values():
        model = config.model
        if model is not None:
            labels.add(model._meta.label)
    return labels


@require_GET
def object_options(request):
    """Return ``{"results": [{id, text}]}`` for a configured context model."""
    user = getattr(request, "user", None)
    if not (user and user.is_staff):
        raise Http404

    label = request.GET.get("model", "")
    if label not in _allowed_labels():
        raise Http404

    try:
        limit = int(request.GET.get("limit", 50) or 50)
    except (TypeError, ValueError):
        limit = 50
    limit = max(1, min(limit, 500))

    model = resolve_model(label)
    return JsonResponse(
        {
            "results": model_options(
                model,
                query=request.GET.get("q", ""),
                limit=limit,
            )
        }
    )


@require_POST
def action(request, action_key):
    """Run a configured action and follow its response."""
    response = run_action(request, action_key)
    _add_confirmation(request)
    if response is None:
        return redirect(request.META.get("HTTP_REFERER") or "/")
    return response


@require_GET
def feed_items(request, pk):
    """Return a rendered slice of a feed (used by filters and infinite scroll)."""
    from ..feeds.models import Feed

    try:
        feed = Feed.objects.get(pk=pk)
    except Feed.DoesNotExist as exc:
        raise Http404 from exc

    try:
        offset = int(request.GET.get("offset", 0) or 0)
    except (TypeError, ValueError):
        offset = 0

    data = render_feed(feed, request, offset=offset)
    return JsonResponse(
        {
            "html": data["items_html"],
            "next_offset": data["next_offset"],
            "has_more": data["has_more"],
            "total": data["total"],
        }
    )
