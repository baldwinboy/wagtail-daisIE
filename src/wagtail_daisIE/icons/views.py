from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .registry import get_provider, render_icon, search_icons
from .value import split_icon


def _preview(value):
    """Return preview HTML for a picker tile.

    Iconify icons use the client-side web component so the picker stays fast;
    everything else is rendered server-side.
    """
    prefix, _name = split_icon(value)
    if prefix:
        provider = get_provider(prefix)
        if provider is not None and provider.kind == "iconify":
            return f'<iconify-icon class="daisyui-icon" icon="{value}"></iconify-icon>'
    return render_icon(value)


@staff_member_required
@require_GET
def icon_search(request):
    query = (request.GET.get("q") or "").strip()
    prefix = (request.GET.get("prefix") or "").strip()
    prefix_param = request.GET.get("prefixes")
    prefixes = [p for p in prefix_param.split(",") if p] if prefix_param else None

    try:
        limit = int(request.GET.get("limit", 64))
    except (TypeError, ValueError):
        limit = 64
    limit = min(max(limit, 1), 999)

    try:
        start = max(int(request.GET.get("start", 0)), 0)
    except (TypeError, ValueError):
        start = 0

    if prefix:
        provider = get_provider(prefix)
        if provider is None:
            icons = []
        elif query:
            icons = provider.search(query, limit=limit, start=start)
        else:
            icons = provider.browse(limit=limit)
    else:
        icons = search_icons(query, prefixes=prefixes, limit=limit, start=start)

    for icon in icons:
        icon["preview"] = _preview(icon["value"])

    return JsonResponse({"icons": icons, "query": query})
