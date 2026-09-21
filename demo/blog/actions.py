"""Session basket actions for the demo (a cart parallel).

Registered in ``WAGTAIL_DAISIE_ACTIONS`` and used by the demo's action buttons.
"""

from django.shortcuts import redirect

SESSION_KEY = "bread_basket"


def _basket_ids(request):
    return list(request.session.get(SESSION_KEY, []))


def _back(request, flag=""):
    url = request.META.get("HTTP_REFERER") or "/"
    if flag:
        url = f"{url}{'&' if '?' in url else '?'}{flag}"
    return url


def basket_items(request, page=None):
    from blog.models import Bread

    ids = _basket_ids(request)
    if not ids:
        return Bread.objects.none()
    return Bread.objects.filter(pk__in=ids)


def basket_count(request, page=None):
    return len(_basket_ids(request))


def basket_add(request, data):
    from blog.models import Bread

    try:
        pk = int(data.get("target", ""))
    except (TypeError, ValueError):
        pk = None
    if pk and Bread.objects.filter(pk=pk).exists():
        ids = _basket_ids(request)
        if pk not in ids:
            ids.append(pk)
            request.session[SESSION_KEY] = ids
    return redirect(_back(request, "basket_added=1"))


def basket_remove(request, data):
    try:
        pk = int(data.get("target", ""))
    except (TypeError, ValueError):
        pk = None
    request.session[SESSION_KEY] = [i for i in _basket_ids(request) if i != pk]
    return redirect(_back(request, "basket_removed=1"))


def basket_clear(request, data):
    request.session[SESSION_KEY] = []
    return redirect(_back(request, "basket_cleared=1"))
