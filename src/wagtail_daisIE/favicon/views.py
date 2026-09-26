"""Public views serving the web-app manifest, browser config and favicon."""

from __future__ import annotations

from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.template.response import TemplateResponse

from ..models import DaisyUIFavicon


def _current(request):
    favicon = DaisyUIFavicon.for_request(request)
    if favicon is None or not favicon.image:
        raise Http404
    return favicon


def manifest(request):
    """Return ``manifest.json`` for the current site."""
    return JsonResponse(_current(request).manifest())


def browser_config(request):
    """Return the Microsoft ``browserconfig.xml`` tile definition."""
    favicon = _current(request)
    return TemplateResponse(
        request,
        "wagtail_daisIE/favicon/browser-config.xml",
        {
            "theme_color": favicon.theme_color,
            "icon_70": favicon.rendition_url("70x70"),
            "icon_150": favicon.rendition_url("150x150"),
            "icon_310": favicon.rendition_url("310x310"),
        },
        content_type="application/xml",
    )


def favicon(request):
    """Redirect ``/favicon.ico`` to the 32x32 rendition."""
    return HttpResponseRedirect(_current(request).rendition_url("32x32"))
