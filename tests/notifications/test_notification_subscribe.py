import pytest

from django.core.cache import cache
from django.test import Client
from django.urls import reverse

from wagtail_daisIE.notifications.models import Audience, AudienceMember


pytestmark = pytest.mark.django_db

SUBSCRIBE_URL = reverse("wagtail_daisIE_notifications:subscribe")


@pytest.fixture
def audience():
    return Audience.objects.create(name="Newsletter")


class TestSubscribe:
    def test_creates_idempotent_and_reactivates(self, audience):
        client = Client()
        data = {"audience": audience.pk, "email": "ada@example.com"}
        response = client.post(SUBSCRIBE_URL, data)
        assert response.status_code == 302
        assert AudienceMember.objects.filter(
            audience=audience, email="ada@example.com"
        ).exists()

        # The endpoint rate-limits one POST per IP per minute.
        cache.clear()
        client.post(SUBSCRIBE_URL, data)
        assert AudienceMember.objects.filter(audience=audience).count() == 1

        member = AudienceMember.objects.get(audience=audience)
        member.is_active = False
        member.save()
        cache.clear()
        client.post(SUBSCRIBE_URL, data)
        member.refresh_from_db()
        assert member.is_active is True

    def test_json_response_and_rule_rejection(self, audience):
        response = Client().post(
            SUBSCRIBE_URL,
            {"audience": audience.pk, "email": "ada@example.com"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert response.status_code == 200 and response.json()["ok"] is True

        rule = Audience.objects.create(
            name="Subs", kind=Audience.Kind.RULE, rule_key="subs"
        )
        cache.clear()
        response = Client().post(
            SUBSCRIBE_URL,
            {"audience": rule.pk, "email": "ada@example.com"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert response.status_code == 400 and response.json()["ok"] is False

    def test_rate_limited(self, audience):
        client = Client()
        data = {"audience": audience.pk, "email": "ada@example.com"}
        first = client.post(SUBSCRIBE_URL, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        second = client.post(
            SUBSCRIBE_URL,
            {"audience": audience.pk, "email": "bob@example.com"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert first.status_code == 200
        assert second.status_code == 429
