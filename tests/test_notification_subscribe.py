import pytest

from django.test import Client
from django.urls import reverse

from wagtail_daisIE.notifications.models import Audience, AudienceMember


pytestmark = pytest.mark.django_db

SUBSCRIBE_URL = reverse("wagtail_daisIE_notifications:subscribe")


@pytest.fixture
def audience():
    return Audience.objects.create(name="Newsletter")


class TestSubscribe:
    def test_creates_member(self, audience):
        client = Client()
        response = client.post(
            SUBSCRIBE_URL, {"audience": audience.pk, "email": "ada@example.com"}
        )
        assert response.status_code == 302
        assert AudienceMember.objects.filter(
            audience=audience, email="ada@example.com"
        ).exists()

    def test_is_idempotent(self, audience):
        client = Client()
        data = {"audience": audience.pk, "email": "ada@example.com"}
        client.post(SUBSCRIBE_URL, data)
        client.post(SUBSCRIBE_URL, data)
        assert AudienceMember.objects.filter(audience=audience).count() == 1

    def test_reactivates_inactive_member(self, audience):
        member = AudienceMember.objects.create(
            audience=audience, email="ada@example.com", is_active=False
        )
        Client().post(
            SUBSCRIBE_URL, {"audience": audience.pk, "email": "ada@example.com"}
        )
        member.refresh_from_db()
        assert member.is_active is True

    def test_json_response(self, audience):
        response = Client().post(
            SUBSCRIBE_URL,
            {"audience": audience.pk, "email": "ada@example.com"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_rejects_rule_audience(self):
        audience = Audience.objects.create(
            name="Subs", kind=Audience.Kind.RULE, rule_key="subs"
        )
        response = Client().post(
            SUBSCRIBE_URL,
            {"audience": audience.pk, "email": "ada@example.com"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert response.status_code == 400
        assert response.json()["ok"] is False

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

    def test_get_not_allowed(self):
        assert Client().get(SUBSCRIBE_URL).status_code == 405
