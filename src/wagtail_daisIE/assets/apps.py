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


class AssetsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "wagtail_daisIE_assets"
    name = "wagtail_daisIE.assets"
    verbose_name = "Wagtail DaisyUI Assets"

    def ready(self):
        post_migrate.connect(
            _seed_icon_sources,
            sender=self,
            dispatch_uid="wagtail_daisIE_assets.seed_icon_sources",
        )
