"""Sending campaigns: audience resolution, delivery and recurrence."""

from __future__ import annotations

import calendar
import logging

from datetime import timedelta

from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from .conf import get_from_email
from .models import CampaignRecipientLog, EmailCampaign


logger = logging.getLogger(__name__)


def recipient_email(recipient):
    if isinstance(recipient, str):
        return recipient
    return getattr(recipient, "email", "") or ""


def add_months(value, months):
    """Return ``value`` advanced by ``months`` calendar months."""
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def next_run_after(value, recurrence):
    """Return the next scheduled time for a recurrence, or ``None``."""
    if recurrence == EmailCampaign.Recurrence.DAILY:
        return value + timedelta(days=1)
    if recurrence == EmailCampaign.Recurrence.WEEKLY:
        return value + timedelta(weeks=1)
    if recurrence == EmailCampaign.Recurrence.MONTHLY:
        return add_months(value, 1)
    return None


def send_campaign(campaign, *, dry_run=False, force=False):
    """Send ``campaign`` to its audience.

    Returns a stats mapping. Re-sending a campaign that is already ``sent`` is a
    no-op unless ``force`` is set; per-recipient logs keep delivery idempotent.
    """
    campaign = EmailCampaign.objects.get(pk=campaign.pk)
    totals = {"sent": 0, "failed": 0, "skipped": 0, "total": 0, "dry_run": dry_run}

    if campaign.status == EmailCampaign.Status.SENT and not force:
        return {**totals, "status": "already-sent"}

    template = campaign.template
    payload = campaign.get_payload()
    recipients = campaign.audience.get_recipients()
    totals["total"] = len(recipients)

    if not dry_run:
        campaign.status = EmailCampaign.Status.SENDING
        campaign.save(update_fields=["status"])

    sent = failed = skipped = 0
    for recipient in recipients:
        email = recipient_email(recipient)
        if not email:
            skipped += 1
            continue

        existing = (
            CampaignRecipientLog.objects.filter(
                campaign=campaign, recipient_email=email
            )
            .values_list("status", flat=True)
            .first()
        )
        if existing == CampaignRecipientLog.Status.SENT and not force:
            skipped += 1
            continue

        if dry_run:
            sent += 1
            continue

        try:
            rendered = template.render(payload=payload, recipient=recipient)
            message = EmailMultiAlternatives(
                rendered.subject,
                rendered.text,
                get_from_email(),
                [email],
            )
            if rendered.html:
                message.attach_alternative(rendered.html, "text/html")
            message.send()
        except Exception as exc:
            failed += 1
            CampaignRecipientLog.objects.update_or_create(
                campaign=campaign,
                recipient_email=email,
                defaults={
                    "status": CampaignRecipientLog.Status.FAILED,
                    "error": str(exc),
                    "sent_at": None,
                },
            )
            continue

        sent += 1
        CampaignRecipientLog.objects.update_or_create(
            campaign=campaign,
            recipient_email=email,
            defaults={
                "status": CampaignRecipientLog.Status.SENT,
                "error": "",
                "sent_at": timezone.now(),
            },
        )

    totals.update({"sent": sent, "failed": failed, "skipped": skipped})

    if not dry_run:
        campaign.sent_count = sent
        campaign.failed_count = failed
        campaign.last_sent_at = timezone.now()
        if campaign.recurrence != EmailCampaign.Recurrence.NONE and sent and not failed:
            campaign.scheduled_at = next_run_after(
                campaign.scheduled_at or timezone.now(), campaign.recurrence
            )
            campaign.status = EmailCampaign.Status.SCHEDULED
        else:
            campaign.status = EmailCampaign.Status.SENT
        campaign.save(
            update_fields=[
                "sent_count",
                "failed_count",
                "last_sent_at",
                "scheduled_at",
                "status",
            ]
        )
        totals["status"] = campaign.status

    return totals


def due_campaigns(now=None):
    """Return scheduled campaigns that are due."""
    now = now or timezone.now()
    return EmailCampaign.objects.filter(
        status=EmailCampaign.Status.SCHEDULED,
        scheduled_at__isnull=False,
        scheduled_at__lte=now,
    )
