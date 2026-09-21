from datetime import datetime, timedelta

import pytest

from django.core.management import call_command
from django.utils import timezone

from wagtail_daisIE.emails.models import EmailTemplate
from wagtail_daisIE.models import DaisyUITheme
from wagtail_daisIE.notifications.campaigns import (
    add_months,
    next_run_after,
    send_campaign,
)
from wagtail_daisIE.notifications.models import (
    Audience,
    AudienceMember,
    CampaignRecipientLog,
    EmailCampaign,
)


pytestmark = pytest.mark.django_db


def _template():
    theme, _created = DaisyUITheme.objects.get_or_create(
        name="campaign-theme", defaults={"default": True}
    )
    template = EmailTemplate.objects.create(
        name="Campaign email", subject="Hello {{ payload.name }}"
    )
    template.email_theme = theme
    template.content = [
        {
            "type": "section",
            "value": {
                "design": {},
                "content": [
                    {
                        "type": "text",
                        "value": {"text": "Hi {{ recipient.email }}", "design": {}},
                    }
                ],
            },
        }
    ]
    template.save()
    return template


def _audience():
    audience = Audience.objects.create(name="Campaign audience")
    AudienceMember.objects.create(audience=audience, email="ada@example.com")
    AudienceMember.objects.create(audience=audience, email="bob@example.com")
    return audience


def _campaign(**kwargs):
    defaults = {
        "name": "Welcome",
        "template": _template(),
        "audience": _audience(),
        "status": EmailCampaign.Status.SCHEDULED,
        "scheduled_at": timezone.now() - timedelta(minutes=5),
    }
    defaults.update(kwargs)
    return EmailCampaign.objects.create(**defaults)


class TestSend:
    def test_sends_to_audience(self, mailoutbox):
        campaign = _campaign()
        stats = send_campaign(campaign)
        assert stats["sent"] == 2
        assert len(mailoutbox) == 2
        campaign.refresh_from_db()
        assert campaign.status == EmailCampaign.Status.SENT
        assert campaign.sent_count == 2
        assert CampaignRecipientLog.objects.filter(campaign=campaign).count() == 2

    def test_dry_run_does_not_send(self, mailoutbox):
        campaign = _campaign()
        stats = send_campaign(campaign, dry_run=True)
        assert stats["sent"] == 2
        assert mailoutbox == []
        campaign.refresh_from_db()
        assert campaign.status == EmailCampaign.Status.SCHEDULED

    def test_already_sent_is_noop(self, mailoutbox):
        campaign = _campaign()
        send_campaign(campaign)
        mailoutbox.clear()
        stats = send_campaign(campaign)
        assert stats["status"] == "already-sent"
        assert mailoutbox == []

    def test_force_resends(self, mailoutbox):
        campaign = _campaign()
        send_campaign(campaign)
        mailoutbox.clear()
        stats = send_campaign(campaign, force=True)
        assert stats["sent"] == 2
        assert len(mailoutbox) == 2

    def test_recurrence_reschedules(self, mailoutbox):
        campaign = _campaign(recurrence=EmailCampaign.Recurrence.WEEKLY)
        scheduled_at = campaign.scheduled_at
        send_campaign(campaign)
        campaign.refresh_from_db()
        assert campaign.status == EmailCampaign.Status.SCHEDULED
        assert campaign.scheduled_at > scheduled_at


class TestRecurrence:
    def test_next_run_after(self):
        base = datetime(2026, 1, 31, 12, 0)
        assert next_run_after(base, EmailCampaign.Recurrence.DAILY) == (
            base + timedelta(days=1)
        )
        assert next_run_after(base, EmailCampaign.Recurrence.WEEKLY) == (
            base + timedelta(weeks=1)
        )
        assert next_run_after(base, EmailCampaign.Recurrence.MONTHLY).month == 2
        assert next_run_after(base, EmailCampaign.Recurrence.NONE) is None

    def test_add_months_clamps_day(self):
        assert add_months(datetime(2026, 1, 31), 1) == datetime(2026, 2, 28)
        assert add_months(datetime(2026, 12, 15), 1) == datetime(2027, 1, 15)


class TestCommand:
    def test_send_campaigns_dry_run(self, capsys):
        _campaign(name="Due campaign")
        call_command("send_campaigns", "--dry-run")
        output = capsys.readouterr().out
        assert "[dry-run]" in output
