"""Render admin-designed error pages and Django error handlers.

Projects opt in from ``urls.py``::

    handler400 = "wagtail_daisIE.errors.handlers.handler400"
    handler403 = "wagtail_daisIE.errors.handlers.handler403"
    handler404 = "wagtail_daisIE.errors.handlers.handler404"
    handler500 = "wagtail_daisIE.errors.handlers.handler500"
"""

from __future__ import annotations

import logging

from django.shortcuts import render

from .models import ErrorPage


logger = logging.getLogger(__name__)

ERROR_TEMPLATE = "wagtail_daisIE/errors/error_page.html"

#: Status codes that Django calls with an ``exception`` argument.
EXCEPTION_STATUS_HANDLERS = {400, 401, 403, 404, 429}


def get_error_page(status_code):
    """Return the active :class:`ErrorPage` for ``status_code``, if any."""
    try:
        return ErrorPage.objects.filter(status_code=status_code, is_active=True).first()
    except Exception:  # pragma: no cover - table may not exist yet
        logger.debug("Could not load error page for %s", status_code, exc_info=True)
        return None


def get_error_theme(error_page):
    from ..models import DaisyUITheme

    try:
        if error_page is not None and error_page.page_theme_id:
            return error_page.page_theme
        return DaisyUITheme.objects.filter(default=True).first()
    except Exception:  # pragma: no cover - defensive
        return None


def render_error_page(request, status_code, *, template=ERROR_TEMPLATE):
    """Render the designed error page (or the bundled fallback) with ``status_code``."""
    error_page = get_error_page(status_code)
    context = {
        "request": request,
        "error_page": error_page,
        "status_code": status_code,
        "daisyui_theme": get_error_theme(error_page),
    }
    return render(request, template, context, status=status_code)


def handler400(request, exception=None):
    return render_error_page(request, 400)


def handler401(request, exception=None):
    return render_error_page(request, 401)


def handler403(request, exception=None):
    return render_error_page(request, 403)


def handler404(request, exception=None):
    return render_error_page(request, 404)


def handler429(request, exception=None):
    return render_error_page(request, 429)


def handler500(request):
    return render_error_page(request, 500)
