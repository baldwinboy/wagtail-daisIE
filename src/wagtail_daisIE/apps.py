import logging

from django.apps import AppConfig
from django.db.models.signals import post_migrate


logger = logging.getLogger(__name__)


def _seed_icon_sources(sender, **kwargs):
    """Ensure the default icon sources exist after migrations."""
    from .models import DaisyUIIconSource

    try:
        DaisyUIIconSource.ensure_defaults()
    except Exception:  # pragma: no cover - table may not be ready yet
        logger.debug("Could not seed default icon sources", exc_info=True)


class WagtailDaisIEAppConfig(AppConfig):
    label = "wagtail_daisIE"
    name = "wagtail_daisIE"
    verbose_name = "Wagtail DaisyUI Interface Editor"

    def ready(self):
        # Register telepath adapters for the DaisyUI admin widgets.
        from . import telepath  # noqa: F401

        post_migrate.connect(
            _seed_icon_sources,
            sender=self,
            dispatch_uid="wagtail_daisIE.seed_icon_sources",
        )

        super().ready()
