import logging

from django.apps import AppConfig


logger = logging.getLogger(__name__)


class WagtailDaisIEAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "wagtail_daisIE"
    name = "wagtail_daisIE"
    verbose_name = "Wagtail DaisyUI Interface Editor"

    def ready(self):
        # Register system checks (e.g. htmx wiring).
        # Register telepath adapters for the DaisyUI admin widgets.
        from . import (
            checks,  # noqa: F401
            telepath,  # noqa: F401
        )

        # Register context-model placeholder documentation for admin help.
        from .dynamic import panels  # noqa: F401

        # Connect model detail-page bridges from project settings.
        try:
            from .detail_pages import bridges as detail_bridges

            detail_bridges.connect_signals()
        except Exception:
            logger.exception("Could not connect detail page bridges")

        # Connect approval workflow callbacks from project settings.
        try:
            from .approval import bridges as approval_bridges

            approval_bridges.connect_signals()
        except Exception:
            logger.exception("Could not connect approval workflow bridges")

        super().ready()
