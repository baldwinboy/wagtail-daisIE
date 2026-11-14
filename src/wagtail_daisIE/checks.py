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
    """Warn when the JIT middleware has no usable compiler."""
    if "wagtail_daisIE.middleware.TailwindCSSMiddleware" not in getattr(
        settings, "MIDDLEWARE", []
    ):
        return []
    if getattr(settings, "TAILWIND_CSS_API", ""):
        return []
    if "django_tailwind_cli" not in getattr(settings, "INSTALLED_APPS", []):
        return [
            Warning(
                "TailwindCSSMiddleware is enabled but neither TAILWIND_CSS_API "
                "nor django_tailwind_cli is configured; runtime CSS will not "
                "be generated.",
                id="wagtail_daisIE.W003",
            )
        ]
    if not getattr(settings, "TAILWIND_CLI_USE_DAISY_UI", False):
        return [
            Warning(
                "django_tailwind_cli is configured without "
                "TAILWIND_CLI_USE_DAISY_UI; the compiler cannot resolve the "
                "daisyui plugin.",
                id="wagtail_daisIE.W004",
            )
        ]
    return []


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
