"""Send due (or a specific) email campaign.

Use from cron::

    python manage.py send_campaigns

or from Celery Beat / a worker via
``wagtail_daisIE.notifications.tasks.run_scheduled_campaigns``.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from wagtail_daisIE.notifications.campaigns import due_campaigns, send_campaign
from wagtail_daisIE.notifications.models import EmailCampaign


class Command(BaseCommand):
    help = "Send scheduled email campaigns that are due."

    def add_arguments(self, parser):
        parser.add_argument(
            "--campaign",
            type=int,
            help="Send a specific campaign by id (regardless of schedule).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be sent without sending.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-send even if the campaign or recipients were already sent.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Maximum number of campaigns to process.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]

        if options["campaign"]:
            campaigns = EmailCampaign.objects.filter(pk=options["campaign"])
        else:
            campaigns = due_campaigns(timezone.now()).order_by("scheduled_at")

        if options["limit"]:
            campaigns = campaigns[: options["limit"]]

        processed = 0
        for campaign in campaigns:
            stats = send_campaign(campaign, dry_run=dry_run, force=force)
            processed += 1
            prefix = "[dry-run] " if dry_run else ""
            self.stdout.write(
                f"{prefix}{campaign.name}: "
                f"{stats['sent']} sent, {stats['failed']} failed, "
                f"{stats['skipped']} skipped of {stats['total']}"
            )

        if not processed:
            self.stdout.write("No campaigns to send.")
