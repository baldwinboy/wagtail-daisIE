import json

from datetime import timedelta
from types import SimpleNamespace

import pytest

from django.contrib.auth import get_user_model
from django.http import HttpResponse, QueryDict
from django.test import RequestFactory
from django.utils import timezone

from wagtail_daisIE.dynamic.actions import (
    get_action_choices,
    resolve_action,
    run_action,
)
from wagtail_daisIE.dynamic.blocks_data import ActionButtonBlock, CalendarBlock
from wagtail_daisIE.dynamic.feeds import apply_filters, render_feed
from wagtail_daisIE.dynamic.models import Feed
from wagtail_daisIE.dynamic.registry import get_context_model, reset_context_models


pytestmark = pytest.mark.django_db

USER_MODEL = get_user_model()


@pytest.fixture(autouse=True)
def _registry(settings):
    settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
        "user": {"label": "User", "model": "auth.User", "source": "request.user"},
    }
    reset_context_models()
    yield
    reset_context_models()


class TestActions:
    def test_choices_and_resolution(self, settings):
        settings.WAGTAIL_DAISIE_ACTIONS = {
            "demo": {
                "label": "Demo",
                "handler": "wagtail_daisIE.test.notifications.fixed_recipients",
            }
        }
        assert ("demo", "Demo") in get_action_choices()
        assert callable(resolve_action("demo"))
        assert resolve_action("missing") is None

    def test_run_action(self, settings, rf):
        def handler(request, data):
            return HttpResponse(f"ok:{data.get('target')}")

        settings.WAGTAIL_DAISIE_ACTIONS = {"demo": {"handler": handler}}
        request = rf.post("/daisie/actions/demo/", {"target": "7"})
        assert run_action(request, "demo").content == b"ok:7"

    def test_unknown_action_raises(self, settings, rf):
        from django.http import Http404

        settings.WAGTAIL_DAISIE_ACTIONS = {}
        with pytest.raises(Http404):
            run_action(rf.post("/x/"), "nope")


class TestActionButtonBlock:
    def test_url_is_resolved(self):
        context = ActionButtonBlock().get_context(
            {"action": "demo", "label": "Go", "design": {}, "audience": {}}
        )
        assert context["action_url"] == "/daisie/actions/demo/"


class TestCalendarBlock:
    def test_groups_events_by_date(self):
        now = timezone.now()
        USER_MODEL.objects.create(username="ada", date_joined=now)
        USER_MODEL.objects.create(username="bob", date_joined=now + timedelta(days=1))
        context = CalendarBlock().get_context(
            {
                "context_model": "user",
                "date_field": "date_joined",
                "event": [
                    {
                        "type": "header",
                        "value": {
                            "text": "{{ user.username }}",
                            "design": {},
                            "audience": {},
                        },
                    }
                ],
                "limit": 50,
                "empty_message": "",
                "design": {},
                "audience": {},
            }
        )
        assert context["days"]
        assert "ada" in "".join(context["days"][0]["events"])


class TestFilters:
    def _config(self, settings):
        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
            "staff": {
                "label": "Staff",
                "model": "auth.User",
                "filters": {
                    "active": {"type": "boolean", "field": "is_active"},
                    "role": {
                        "type": "choice",
                        "field": "is_staff",
                        "choices": [("1", "Staff")],
                    },
                    "groups": {
                        "type": "choice",
                        "multi": True,
                        "field": "pk",
                        "choices": [],
                    },
                    "joined": {"type": "date_range", "field": "date_joined"},
                    "username": {"type": "search", "fields": ["username"]},
                },
            }
        }
        reset_context_models()
        return get_context_model("staff")

    def test_boolean(self, settings):
        config = self._config(settings)
        USER_MODEL.objects.create(username="active", is_active=True)
        USER_MODEL.objects.create(username="inactive", is_active=False)
        result = apply_filters(
            USER_MODEL.objects.all(), config, QueryDict("filter_active=0")
        )
        assert list(result.values_list("username", flat=True)) == ["inactive"]

    def test_choice(self, settings):
        config = self._config(settings)
        staff = USER_MODEL.objects.create(username="staff", is_staff=True)
        USER_MODEL.objects.create(username="regular")
        result = apply_filters(
            USER_MODEL.objects.all(), config, QueryDict("filter_role=1")
        )
        assert list(result) == [staff]

    def test_multi_choice(self, settings):
        config = self._config(settings)
        first = USER_MODEL.objects.create(username="a")
        second = USER_MODEL.objects.create(username="b")
        USER_MODEL.objects.create(username="c")
        params = QueryDict(f"filter_groups={first.pk}&filter_groups={second.pk}")
        assert apply_filters(USER_MODEL.objects.all(), config, params).count() == 2

    def test_date_range(self, settings):
        config = self._config(settings)
        old = USER_MODEL.objects.create(username="old")
        USER_MODEL.objects.filter(pk=old.pk).update(
            date_joined=timezone.now() - timedelta(days=30)
        )
        USER_MODEL.objects.create(username="new")
        params = QueryDict(f"filter_joined_from={timezone.now().date()}")
        assert apply_filters(USER_MODEL.objects.all(), config, params).count() == 1

    def test_search(self, settings):
        config = self._config(settings)
        USER_MODEL.objects.create(username="findme")
        USER_MODEL.objects.create(username="other")
        params = QueryDict("feed_search=find")
        result = apply_filters(USER_MODEL.objects.all(), config, params)
        assert list(result.values_list("username", flat=True)) == ["findme"]

    def test_invalid_value_is_ignored(self, settings):
        config = self._config(settings)
        USER_MODEL.objects.create(username="ada")
        params = QueryDict("filter_active=not-a-bool")
        assert apply_filters(USER_MODEL.objects.all(), config, params).count() == 1


class TestFeedRendering:
    def _feed(self, **kwargs):
        defaults = {
            "name": "Users",
            "context_model": "user",
            "order_by": "username",
            "page_size": 9,
        }
        defaults.update(kwargs)
        feed = Feed.objects.create(**defaults)
        feed.item = [
            {
                "type": "header",
                "value": {"text": "{{ user.username }}", "design": {}, "audience": {}},
            }
        ]
        feed.save()
        return feed

    def test_renders_items(self):
        USER_MODEL.objects.create(username="ada")
        USER_MODEL.objects.create(username="bob")
        data = render_feed(self._feed(), RequestFactory().get("/"))
        assert "ada" in data["items_html"]
        assert "bob" in data["items_html"]
        assert data["has_more"] is False
        assert data["total"] == 2

    def test_has_more_and_next_offset(self):
        USER_MODEL.objects.create(username="ada")
        USER_MODEL.objects.create(username="bob")
        feed = self._feed(page_size=1)
        data = render_feed(feed, RequestFactory().get("/"))
        assert data["has_more"] is True
        assert data["next_offset"] == 1
        assert "ada" in data["items_html"]
        assert "bob" not in data["items_html"]

    def test_builds_filters(self, settings):
        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
            "user": {
                "label": "User",
                "model": "auth.User",
                "filters": {
                    "active": {"type": "boolean", "field": "is_active"},
                },
            }
        }
        reset_context_models()
        feed = self._feed()
        feed.filters = [("filter", {"key": "user:active"})]
        feed.save()
        data = render_feed(feed, RequestFactory().get("/"))
        assert data["filters"][0]["key"] == "active"
        assert data["filters"][0]["type"] == "boolean"

    def test_uses_configured_queryset(self, settings):
        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
            "user": {
                "label": "User",
                "model": "auth.User",
                "queryset": lambda request, page: USER_MODEL.objects.filter(
                    is_staff=True
                ),
            }
        }
        reset_context_models()
        USER_MODEL.objects.create(username="staffonly", is_staff=True)
        USER_MODEL.objects.create(username="regularonly")
        data = render_feed(self._feed(), RequestFactory().get("/"))
        assert "staffonly" in data["items_html"]
        assert "regularonly" not in data["items_html"]


class TestFeedEndpoint:
    def test_returns_items_json(self):
        from wagtail_daisIE.dynamic.views import feed_items

        USER_MODEL.objects.create(username="ada")
        feed = Feed.objects.create(name="Users", context_model="user")
        feed.item = [
            {
                "type": "header",
                "value": {"text": "{{ user.username }}", "design": {}, "audience": {}},
            }
        ]
        feed.save()
        response = feed_items(RequestFactory().get("/"), feed.pk)
        payload = json.loads(response.content)
        assert "ada" in payload["html"]


class TestFilterStyling:
    def _feed(self, settings):
        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
            "user": {
                "label": "User",
                "model": "auth.User",
                "filters": {
                    "active": {"type": "boolean", "field": "is_active"},
                    "joined": {"type": "date_range", "field": "date_joined"},
                },
            }
        }
        reset_context_models()
        feed = Feed.objects.create(name="Styled", context_model="user")
        feed.filters = [
            (
                "filter",
                {
                    "key": "user:active",
                    "button_appearance": {
                        "normal": {"color": "btn-primary"},
                        "active": {"color": "btn-secondary"},
                    },
                    "label_design": {"typography": {"font_weight": "font-bold"}},
                },
            ),
            (
                "filter",
                {
                    "key": "user:joined",
                    "input_design": {"typography": {"font_size": "text-sm"}},
                },
            ),
        ]
        feed.submit_appearance = [
            ("appearance", {"normal": {"color": "btn-secondary"}})
        ]
        feed.save()
        return feed

    def test_filter_css(self, settings):
        feed = self._feed(settings)
        data = render_feed(feed, RequestFactory().get("/"))
        by_key = {item["key"]: item for item in data["filters"]}
        assert "btn-primary" in by_key["active"]["button_css"]
        assert "btn-secondary" in by_key["active"]["selected_css"]
        assert "font-bold" in by_key["active"]["label_css"]
        assert "text-sm" in by_key["joined"]["input_css"]

    def test_submit_css(self, settings):
        feed = self._feed(settings)
        data = render_feed(feed, RequestFactory().get("/"))
        assert "btn-secondary" in data["submit_css"]


class TestDateTransform:
    def _config(self, field_instance):
        class Meta:
            @staticmethod
            def get_field(name):
                return field_instance

        class Model:
            _meta = Meta

        return SimpleNamespace(model=Model)

    def test_date_field_uses_field(self):
        from django.db.models import DateField

        from wagtail_daisIE.dynamic.feeds import _date_transform

        assert _date_transform(self._config(DateField()), "published") == "published"

    def test_datetime_field_uses_date_transform(self):
        from django.db.models import DateTimeField

        from wagtail_daisIE.dynamic.feeds import _date_transform

        assert (
            _date_transform(self._config(DateTimeField()), "published")
            == "published__date"
        )


class TestDatetimeRange:
    def test_date_range_on_datetime_field(self, settings):
        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
            "person": {
                "label": "Person",
                "model": "auth.User",
                "filters": {
                    "joined": {"type": "date_range", "field": "date_joined"},
                },
            }
        }
        reset_context_models()
        old = USER_MODEL.objects.create(username="old")
        USER_MODEL.objects.filter(pk=old.pk).update(
            date_joined=timezone.now() - timedelta(days=30)
        )
        USER_MODEL.objects.create(username="new")

        config = get_context_model("person")
        from_date = (timezone.now() - timedelta(days=1)).date().isoformat()
        params = QueryDict(f"filter_joined_from={from_date}")
        result = apply_filters(USER_MODEL.objects.all(), config, params)
        assert list(result.values_list("username", flat=True)) == ["new"]
