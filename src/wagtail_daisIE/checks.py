"""System checks for optional-but-recommended project wiring."""

from django.conf import settings
from django.core.checks import Error, Warning, register


@register()
def check_htmx_middleware(app_configs, **kwargs):
    """Warn when the htmx integration is on but not wired up.

    ``wagtail_daisIE`` ships htmx-enhanced blocks; they degrade to plain
    forms/links without JavaScript, but the async behaviour needs
    ``django_htmx`` installed and its middleware enabled.
    """
    if not getattr(settings, "WAGTAIL_DAISIE_HTMX", True):
        return []
    errors = []
    if "django_htmx" not in getattr(settings, "INSTALLED_APPS", []):
        errors.append(
            Warning(
                "WAGTAIL_DAISIE_HTMX is enabled but 'django_htmx' is not in "
                "INSTALLED_APPS; htmx-enhanced blocks will not be included.",
                id="wagtail_daisIE.W001",
            )
        )
    if "django_htmx.middleware.HtmxMiddleware" not in getattr(
        settings, "MIDDLEWARE", []
    ):
        errors.append(
            Warning(
                "WAGTAIL_DAISIE_HTMX is enabled but "
                "'django_htmx.middleware.HtmxMiddleware' is not in MIDDLEWARE; "
                "views cannot detect htmx requests.",
                id="wagtail_daisIE.W002",
            )
        )
    return errors


@register()
def check_tailwind_compiler(app_configs, **kwargs):
    """Validate the runtime Tailwind compiler configuration."""
    if "wagtail_daisIE.middleware.TailwindCSSMiddleware" not in getattr(
        settings, "MIDDLEWARE", []
    ):
        return []

    from importlib.util import find_spec

    from django.contrib.staticfiles import finders
    from django.urls import NoReverseMatch, reverse

    from .tailwindcss.api import get_tailwind_api, tailwind_api_error
    from .tailwindcss.placeholder import BASE_CSS_STATIC_PATH

    warnings = []
    api = get_tailwind_api()
    api_error = tailwind_api_error()
    has_cli = find_spec("django_tailwind_cli") is not None

    if api_error:
        warnings.append(Warning(api_error, id="wagtail_daisIE.W006"))
    if api is None and not has_cli:
        warnings.append(
            Warning(
                "TailwindCSSMiddleware is enabled but neither a valid "
                "TAILWIND_CSS_API nor django_tailwind_cli is configured; "
                "runtime CSS will not be generated.",
                id="wagtail_daisIE.W003",
            )
        )
    if (
        api is None
        and has_cli
        and not getattr(settings, "TAILWIND_CLI_USE_DAISY_UI", False)
    ):
        warnings.append(
            Warning(
                "django_tailwind_cli is configured without "
                "TAILWIND_CLI_USE_DAISY_UI; the compiler cannot resolve the "
                "daisyui plugin.",
                id="wagtail_daisIE.W004",
            )
        )
    if api is not None and api.transport == "websocket" and api.token:
        warnings.append(
            Warning(
                "Token-protected WebSocket Tailwind APIs cannot be used from "
                "the browser; configure a same-origin proxy or remove the "
                "token.",
                id="wagtail_daisIE.W007",
            )
        )

    for name in ("artifact", "input"):
        try:
            reverse(
                f"wagtail_daisIE_tailwind:{name}",
                kwargs={"token": "0" * 64},
            )
        except NoReverseMatch:
            warnings.append(
                Warning(
                    "The wagtail_daisIE tailwind URLs are not included; add "
                    "path('daisie/tailwind/', include('wagtail_daisIE.tailwindcss.urls')).",
                    id="wagtail_daisIE.W005",
                )
            )
            break

    try:
        if finders.find(BASE_CSS_STATIC_PATH) is None:
            warnings.append(
                Warning(
                    "The committed Tailwind base stylesheet is missing; run "
                    "the build-css utility.",
                    id="wagtail_daisIE.W008",
                )
            )
    except Exception:  # pragma: no cover - storage configuration boundary
        warnings.append(
            Warning(
                "Could not inspect staticfiles finders for the Tailwind base "
                "stylesheet.",
                id="wagtail_daisIE.W008",
            )
        )

    backend = getattr(settings, "CACHES", {}).get("default", {}).get("BACKEND", "")
    if "LocMemCache" in backend:
        warnings.append(
            Warning(
                "The default cache is LocMemCache. Tailwind artifact URLs and "
                "background compilation require a shared cache in "
                "multi-process deployments.",
                id="wagtail_daisIE.W009",
            )
        )

    return warnings


@register()
def check_detail_page_configs(app_configs, **kwargs):
    """Validate ``WAGTAIL_DAISIE_DETAIL_PAGES`` without database access."""
    from .detail_pages.exceptions import DetailPageConfigurationError
    from .detail_pages.validation import validate_detail_pages

    try:
        validate_detail_pages(records=False)
    except DetailPageConfigurationError as exc:
        return [Error(str(exc), id="wagtail_daisIE.E001")]
    return []
