from datetime import datetime

import pytest

from wagtail_daisIE.notifications.context import (
    build_context,
    context_from_template_context,
    recipient_from,
)


class TestRecipient:
    def test_from_email_string_and_user_like_object(self):
        recipient = recipient_from("ada@example.com")
        assert recipient.email == "ada@example.com"
        assert recipient.name == "ada@example.com"

        class User:
            email = "ada@example.com"
            first_name = "Ada"
            last_name = "Lovelace"
            username = "ada"
            pk = 7

            def get_full_name(self):
                return "Ada Lovelace"

        recipient = recipient_from(User())
        assert recipient.name == "Ada Lovelace"
        assert recipient.first_name == "Ada" and recipient.username == "ada"
        assert recipient.pk == 7 and recipient.user is not None


class TestBuildContext:
    @pytest.mark.django_db
    def test_includes_named_objects_and_defaults(self):
        site = object()
        context = build_context(
            site=site,
            recipient="ada@example.com",
            payload={"title": "Bread"},
            now=datetime(2026, 11, 12),
        )
        assert context["site"] is site
        assert context["payload"] == {"title": "Bread"}
        assert context["now"] == datetime(2026, 11, 12)
        assert context["recipient"].email == "ada@example.com"
        assert context["user"] is context["recipient"]

        empty = build_context(site=None, payload=None)
        assert empty["payload"] == {} and "now" in empty


class TestContextFromTemplateContext:
    @pytest.mark.django_db
    def test_picks_up_keys_and_fills_defaults(self):
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
        assert context["now"] is now and context["site"] == "site"

        class EmptyContext:
            def get(self, key):
                return None

        defaults = context_from_template_context(EmptyContext())
        assert defaults["payload"] == {} and defaults["now"] is not None
