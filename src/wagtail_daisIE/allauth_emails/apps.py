import logging

from django.apps import AppConfig
from django.db.models.signals import post_migrate


logger = logging.getLogger(__name__)


def _seed_overrides(sender, **kwargs):
    """Ensure an override row exists for every discovered allauth email."""
    from .models import AllauthEmailOverride

    try:
        AllauthEmailOverride.ensure_defaults()
    except Exception:  # pragma: no cover - table may not be ready yet
        logger.debug("Could not seed allauth email overrides", exc_info=True)


class AllauthEmailsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "wagtail_daisIE_allauth_emails"
    name = "wagtail_daisIE.allauth_emails"
    verbose_name = "Wagtail DaisyUI Allauth Emails"

    def ready(self):
        post_migrate.connect(
            _seed_overrides,
            sender=self,
            dispatch_uid="wagtail_daisIE_allauth_emails.seed_overrides",
        )
