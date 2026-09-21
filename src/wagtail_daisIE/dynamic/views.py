"""Admin endpoints backing dynamic context widgets."""

from __future__ import annotations

from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_POST

from .actions import run_action
from .feeds import render_feed
from .registry import get_context_models, resolve_model
from .resolvers import model_options


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
    if response is None:
        return redirect(request.META.get("HTTP_REFERER") or "/")
    return response


@require_GET
def feed_items(request, pk):
    """Return a rendered slice of a feed (used by filters and infinite scroll)."""
    from ..models import Feed

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
