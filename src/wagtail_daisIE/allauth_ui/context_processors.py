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
    """Give allauth requests the default theme standard pages get from a Page.

    Guarded to the allauth URL namespace so normal page requests never pay for
    the query or have their page theme overwritten.
    """
    match = getattr(request, "resolver_match", None)
    if match is None or getattr(match, "namespace", "") != "allauth":
        return {}
    from ..models import DaisyUITheme

    try:
        theme = DaisyUITheme.objects.filter(default=True).first()
    except Exception:  # pragma: no cover - table may not exist
        theme = None
    return {"daisyui_theme": theme}


def chrome_menus(request):
    """Expose the menu names the default chrome base renders."""
    return {
        "header_menu_name": getattr(
            settings, "WAGTAIL_DAISIE_HEADER_MENU", "Main navigation"
        ),
        "footer_menu_name": getattr(settings, "WAGTAIL_DAISIE_FOOTER_MENU", "Footer"),
    }
