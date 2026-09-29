"""Context processors for the allauth page parity feature."""

from __future__ import annotations

from django.conf import settings


#: Package-shipped chrome base used when a project does not point at its own.
DEFAULT_BASE = "wagtail_daisIE/allauth/base.html"


def allauth_base(request):
    """Expose the parent template the allauth layout should extend."""
    return {
        "daisie_auth_base_template": getattr(
            settings, "WAGTAIL_DAISIE_ALLAUTH_BASE_TEMPLATE", DEFAULT_BASE
        )
    }


def allauth_theme(request):
    """Give allauth requests the theme and page override they should render.

    django-allauth is usually mounted without a URL namespace, so the resolved
    view's module (``allauth.*``) is the reliable signal. Guarded to allauth so
    normal page requests never pay for the queries.

    Theme precedence: the active ``AllauthPageOverride`` theme, then the visitor's
    persisted ``daisie_theme`` cookie, then the default theme.
    """
    match = getattr(request, "resolver_match", None)
    module = getattr(getattr(match, "func", None), "__module__", "") or ""
    view_name = getattr(match, "view_name", "") or ""
    if not (module.startswith("allauth") or view_name.startswith("allauth")):
        return {}

    from wagtail.models import Site

    from ..models import DaisyUITheme
    from .models import AllauthPageOverride

    data = {}
    override = None
    try:
        site = Site.find_for_request(request)
        override = AllauthPageOverride.get_active(view_name, site=site)
    except Exception:  # pragma: no cover - table may not exist
        override = None
    if override is not None:
        data["daisie_allauth_override"] = override
        data["daisie_allauth_page_active"] = True

    theme = None
    if override is not None and override.theme_id:
        theme = override.theme
    try:
        if theme is None:
            cookie_name = request.COOKIES.get("daisie_theme")
            if cookie_name:
                theme = DaisyUITheme.objects.filter(name=cookie_name).first()
        if theme is None:
            theme = DaisyUITheme.objects.filter(default=True).first()
    except Exception:  # pragma: no cover - table may not exist
        theme = None

    data["daisyui_theme"] = theme
    return data


def chrome_menus(request):
    """Expose the menu names the default chrome base renders."""
    return {
        "header_menu_name": getattr(
            settings, "WAGTAIL_DAISIE_HEADER_MENU", "Main navigation"
        ),
        "footer_menu_name": getattr(settings, "WAGTAIL_DAISIE_FOOTER_MENU", "Footer"),
    }
