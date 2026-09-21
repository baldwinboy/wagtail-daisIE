from datetime import datetime

import pytest

from wagtail_daisIE.notifications.context import (
    build_context,
    context_from_template_context,
    get_current_site,
    recipient_from,
)


class TestRecipient:
    def test_from_email_string(self):
        recipient = recipient_from("ada@example.com")
        assert recipient.email == "ada@example.com"
        assert recipient.name == "ada@example.com"

    def test_from_user_like_object(self):
        class User:
            email = "ada@example.com"
            first_name = "Ada"
            last_name = "Lovelace"
            username = "ada"
            pk = 7

            def get_full_name(self):
                return "Ada Lovelace"

        recipient = recipient_from(User())
        assert recipient.email == "ada@example.com"
        assert recipient.name == "Ada Lovelace"
        assert recipient.first_name == "Ada"
        assert recipient.username == "ada"
        assert recipient.pk == 7
        assert recipient.user is not None

    def test_none(self):
        assert recipient_from(None) is None


class TestBuildContext:
    def test_includes_named_objects(self):
        site = object()
        recipient = "ada@example.com"
        context = build_context(
            site=site,
            recipient=recipient,
            payload={"title": "Bread"},
            now=datetime(2026, 11, 12),
        )
        assert context["site"] is site
        assert context["payload"] == {"title": "Bread"}
        assert context["now"] == datetime(2026, 11, 12)
        assert context["recipient"].email == "ada@example.com"
        assert context["user"] is context["recipient"]

    @pytest.mark.django_db
    def test_no_site_does_not_raise(self):
        context = build_context(site=None, payload=None)
        assert context["payload"] == {}
        assert "now" in context


class TestContextFromTemplateContext:
    def test_picks_up_known_keys(self):
        class FakeContext:
            def __init__(self, data):
                self._data = data

            def get(self, key):
                return self._data.get(key)

        now = datetime(2026, 11, 12)
        context = context_from_template_context(
            FakeContext({"payload": {"a": 1}, "now": now, "site": "site"})
        )
        assert context["payload"] == {"a": 1}
        assert context["now"] is now
        assert context["site"] == "site"

    @pytest.mark.django_db
    def test_fills_defaults(self):
        class FakeContext:
            def get(self, key):
                return None

        context = context_from_template_context(FakeContext())
        assert context["payload"] == {}
        assert context["now"] is not None


@pytest.mark.django_db
class TestCurrentSite:
    def test_returns_site_or_none(self):
        result = get_current_site()
        assert result is None or result.pk is not None

    def test_uses_explicit_site(self):
        marker = object()
        assert get_current_site(site=marker) is marker
