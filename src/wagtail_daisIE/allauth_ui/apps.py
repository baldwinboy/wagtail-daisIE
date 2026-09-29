import logging

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


logger = logging.getLogger(__name__)


def _seed_page_overrides(sender, **kwargs):
    """Ensure a design row exists for every discovered allauth account view."""
    from .models import AllauthPageOverride

    try:
        AllauthPageOverride.ensure_defaults()
    except Exception:  # pragma: no cover - table may not be ready yet
        logger.debug("Could not seed allauth page overrides", exc_info=True)


class AllauthUIAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "wagtail_daisIE_allauth_ui"
    name = "wagtail_daisIE.allauth_ui"
    verbose_name = "Wagtail DaisyUI Allauth Pages"

    def ready(self):
        # Opt-in DaisyUI styling for allauth pages/forms.
        if getattr(settings, "WAGTAIL_DAISIE_ALLAUTH_UI", False):
            from . import register_template_dir

            register_template_dir()

        post_migrate.connect(
            _seed_page_overrides,
            sender=self,
            dispatch_uid="wagtail_daisIE_allauth_ui.seed_page_overrides",
        )
