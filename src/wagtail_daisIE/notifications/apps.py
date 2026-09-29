import logging

from django.apps import AppConfig


logger = logging.getLogger(__name__)


class NotificationsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "wagtail_daisIE_notifications"
    name = "wagtail_daisIE.notifications"
    verbose_name = "Wagtail DaisyUI Notifications"

    def ready(self):
        # Connect notification bridge signals from project settings.
        try:
            from .bridges import connect_signals

            connect_signals()
        except Exception:
            logger.exception("Could not connect notification bridges")
