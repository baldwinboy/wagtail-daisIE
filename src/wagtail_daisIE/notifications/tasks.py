"""Optional Celery integration for campaigns.

Celery is not a dependency; the task is only wrapped when it is installed. Use
``just``/cron with the ``send_campaigns`` management command otherwise.
"""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)


def run_scheduled_campaigns():
    """Send every due campaign and return ``[(campaign_id, stats), ...]``."""
    from .campaigns import due_campaigns, send_campaign

    results = []
    for campaign in due_campaigns():
        try:
            results.append((campaign.pk, send_campaign(campaign)))
        except Exception:  # pragma: no cover - defensive
            logger.exception("Campaign %s failed", campaign.pk)
    return results


try:  # pragma: no cover - exercised only when celery is installed
    from celery import shared_task

    run_scheduled_campaigns = shared_task(
        name="wagtail_daisIE.run_scheduled_campaigns"
    )(run_scheduled_campaigns)
except ImportError:
    pass
