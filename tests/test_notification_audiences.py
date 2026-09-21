import pytest

from django.contrib.auth import get_user_model

from wagtail_daisIE.base_blocks.audience import (
    get_audience_rule_choices,
    resolve_audience_queryset,
)
from wagtail_daisIE.notifications.models import Audience, AudienceMember


pytestmark = pytest.mark.django_db

USER_MODEL = get_user_model()


class TestManualAudience:
    def test_recipients_and_emails(self):
        audience = Audience.objects.create(name="Newsletter")
        user = USER_MODEL.objects.create(username="ada", email="ada@example.com")
        AudienceMember.objects.create(audience=audience, user=user)
        AudienceMember.objects.create(audience=audience, email="bob@example.com")
        AudienceMember.objects.create(
            audience=audience, email="off@example.com", is_active=False
        )

        recipients = audience.get_recipients()
        assert user in recipients
        assert "bob@example.com" in recipients
        assert "off@example.com" not in audience.get_emails()
        assert set(audience.get_emails()) == {"ada@example.com", "bob@example.com"}

    def test_requires_user_or_email(self):
        from django.db import IntegrityError, transaction

        audience = Audience.objects.create(name="Empty")
        with pytest.raises(IntegrityError), transaction.atomic():
            AudienceMember.objects.create(audience=audience)

    def test_duplicate_email_rejected(self):
        from django.db import IntegrityError, transaction

        audience = Audience.objects.create(name="Dup")
        AudienceMember.objects.create(audience=audience, email="a@b.com")
        with pytest.raises(IntegrityError), transaction.atomic():
            AudienceMember.objects.create(audience=audience, email="a@b.com")


class TestRuleAudience:
    def test_uses_configured_queryset(self, settings):
        staff = USER_MODEL.objects.create(username="staff", is_staff=True)
        USER_MODEL.objects.create(username="regular")
        settings.WAGTAIL_DAISIE_AUDIENCE_RULES = {
            "subs": {
                "label": "Subscribers",
                "rule": lambda request: True,
                "queryset": lambda: USER_MODEL.objects.filter(is_staff=True),
            }
        }
        audience = Audience.objects.create(
            name="Subs", kind=Audience.Kind.RULE, rule_key="subs"
        )
        recipients = audience.get_recipients()
        assert list(recipients) == [staff]

    def test_missing_queryset_returns_empty(self, settings):
        settings.WAGTAIL_DAISIE_AUDIENCE_RULES = {
            "subs": {"label": "Subs", "rule": lambda request: True}
        }
        audience = Audience.objects.create(
            name="No query", kind=Audience.Kind.RULE, rule_key="subs"
        )
        assert audience.get_recipients() == []

    def test_rule_choices(self, settings):
        settings.WAGTAIL_DAISIE_AUDIENCE_RULES = {
            "adults": {"label": "Adults", "rule": lambda request: True}
        }
        assert get_audience_rule_choices() == [("adults", "Adults")]

    def test_resolve_queryset_supports_callable(self, settings):
        settings.WAGTAIL_DAISIE_AUDIENCE_RULES = {
            "adults": {
                "label": "Adults",
                "rule": lambda request: True,
                "queryset": lambda: USER_MODEL.objects.all(),
            }
        }
        assert resolve_audience_queryset("adults") is not None
