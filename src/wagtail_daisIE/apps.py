import logging

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


logger = logging.getLogger(__name__)


def _seed_icon_sources(sender, **kwargs):
    """Ensure the default icon sources exist after migrations."""
    from .models import DaisyUIIconSource

    try:
        DaisyUIIconSource.ensure_defaults()
    except Exception:  # pragma: no cover - table may not be ready yet
        logger.debug("Could not seed default icon sources", exc_info=True)


def _seed_allauth_overrides(sender, **kwargs):
    """Ensure an override row exists for every discovered allauth email."""
    from .notifications.models import AllauthEmailOverride

    try:
        AllauthEmailOverride.ensure_defaults()
    except Exception:  # pragma: no cover - table may not be ready yet
        logger.debug("Could not seed allauth email overrides", exc_info=True)


class WagtailDaisIEAppConfig(AppConfig):
    label = "wagtail_daisIE"
    name = "wagtail_daisIE"
    verbose_name = "Wagtail DaisyUI Interface Editor"

    def ready(self):
        # Register telepath adapters for the DaisyUI admin widgets.
        from . import telepath  # noqa: F401

        # Register context-model placeholder documentation for admin help.
        from .dynamic import panels  # noqa: F401

        # Connect notification bridge signals from project settings.
        try:
            from .notifications import bridges as notification_bridges

            notification_bridges.connect_signals()
        except Exception:
            logger.exception("Could not connect notification bridges")

        # Opt-in DaisyUI styling for allauth pages/forms.
        if getattr(settings, "WAGTAIL_DAISIE_ALLAUTH_UI", False):
            from .allauth_ui import register_template_dir

            register_template_dir()

        post_migrate.connect(
            _seed_icon_sources,
            sender=self,
            dispatch_uid="wagtail_daisIE.seed_icon_sources",
        )

        post_migrate.connect(
            _seed_allauth_overrides,
            sender=self,
            dispatch_uid="wagtail_daisIE.seed_allauth_overrides",
        )

        super().ready()
