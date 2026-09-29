import pytest

from django.contrib.auth import get_user_model

from wagtail_daisIE.base_blocks.audience import get_audience_rule_choices
from wagtail_daisIE.notifications.models import Audience, AudienceMember


pytestmark = pytest.mark.django_db

USER_MODEL = get_user_model()


class TestManualAudience:
    def test_recipients_and_requires_member(self):
        from django.db import IntegrityError, transaction

        audience = Audience.objects.create(name="Newsletter")
        user = USER_MODEL.objects.create(username="ada", email="ada@example.com")
        AudienceMember.objects.create(audience=audience, user=user)
        AudienceMember.objects.create(audience=audience, email="bob@example.com")
        AudienceMember.objects.create(
            audience=audience, email="off@example.com", is_active=False
        )
        assert user in audience.get_recipients()
        assert "bob@example.com" in audience.get_recipients()
        assert set(audience.get_emails()) == {"ada@example.com", "bob@example.com"}

        empty = Audience.objects.create(name="Empty")
        with pytest.raises(IntegrityError), transaction.atomic():
            AudienceMember.objects.create(audience=empty)


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
        assert list(audience.get_recipients()) == [staff]

    def test_rule_choices(self, settings):
        settings.WAGTAIL_DAISIE_AUDIENCE_RULES = {
            "adults": {"label": "Adults", "rule": lambda request: True}
        }
        assert get_audience_rule_choices() == [("adults", "Adults")]
        # A rule without a label still needs a usable choice.
        settings.WAGTAIL_DAISIE_AUDIENCE_RULES = {"adults": {}}
        assert get_audience_rule_choices() == [("adults", "adults")]
        settings.WAGTAIL_DAISIE_AUDIENCE_RULES = {}
        assert get_audience_rule_choices() == []
