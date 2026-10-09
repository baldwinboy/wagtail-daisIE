"""System checks for optional-but-recommended project wiring."""

from django.conf import settings
from django.core.checks import Warning, register


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
