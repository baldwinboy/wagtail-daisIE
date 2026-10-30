import itertools

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
from wagtail_daisIE.dynamic.feeds import (
    apply_filters,
    render_feed,
)
from wagtail_daisIE.dynamic.registry import get_context_model, reset_context_models
from wagtail_daisIE.feeds.blocks_data import ActionBlock, CalendarBlock
from wagtail_daisIE.feeds.models import Feed


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
    def test_choices_resolution_run_and_unknown(self, settings, rf):
        from django.http import Http404

        def handler(request, data):
            return HttpResponse(f"ok:{data.get('target')}")

        settings.WAGTAIL_DAISIE_ACTIONS = {
            "demo": {"label": "Demo", "handler": handler}
        }
        assert ("demo", "Demo") in get_action_choices()
        assert callable(resolve_action("demo"))
        assert resolve_action("missing") is None
        assert run_action(
            rf.post("/daisie/actions/demo/", {"target": "7"}), "demo"
        ).content == (b"ok:7")
        with pytest.raises(Http404):
            run_action(rf.post("/x/"), "nope")


class TestActionBlock:
    def test_url_is_resolved(self):
        context = ActionBlock().get_context(
            {"action": "demo", "button": {}, "design": {}, "audience": {}}
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
        assert [day["iso"] for day in context["days"]] == [
            now.date().isoformat(),
            (now + timedelta(days=1)).date().isoformat(),
        ]
        assert "ada" in "".join(context["days"][0]["events"])
        assert "bob" in "".join(context["days"][1]["events"])


def _query_username(queryset, params, key):
    value = (params.get(f"filter_{key}") or "").strip()
    if value:
        return queryset.filter(username__icontains=value)
    return queryset


def _filter_config(settings):
    settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
        "staff": {
            "label": "Staff",
            "model": "auth.User",
            "filters": {
                "active": {"type": "boolean", "field": "is_active"},
                "groups": {
                    "type": "choice",
                    "multi": True,
                    "field": "pk",
                    "choices": [],
                },
                "joined": {"type": "date_range", "field": "date_joined"},
                "username": {"type": "search", "fields": ["username"]},
                "named": {
                    "type": "choice",
                    "field": "username",
                    "query": _query_username,
                },
            },
        }
    }
    reset_context_models()
    return get_context_model("staff")


class TestFilters:
    def test_boolean_multi_date_range_and_search(self, settings):
        config = _filter_config(settings)
        active = USER_MODEL.objects.create(username="active", is_active=True)
        USER_MODEL.objects.create(username="inactive", is_active=False)
        staffer = USER_MODEL.objects.create(username="staffer", is_staff=True)
        USER_MODEL.objects.create(username="recent")
        old = USER_MODEL.objects.create(username="old")
        USER_MODEL.objects.filter(pk=old.pk).update(
            date_joined=timezone.now() - timedelta(days=30)
        )
        today = timezone.now().date()

        def names(params):
            result = apply_filters(USER_MODEL.objects.all(), config, QueryDict(params))
            return sorted(result.values_list("username", flat=True))

        assert names("filter_active=0") == ["inactive"]
        assert names(f"filter_groups={active.pk}&filter_groups={staffer.pk}") == [
            "active",
            "staffer",
        ]
        assert names(f"filter_joined_from={today}") == [
            "active",
            "inactive",
            "recent",
            "staffer",
        ]
        assert names("feed_search=staff") == ["staffer"]
        # A ``query`` callable can filter on anything (annotations, lookups).
        assert names("filter_named=sta") == ["staffer"]
        # An unknown filter key is ignored rather than erroring.
        assert names("filter_nope=1") == [
            "active",
            "inactive",
            "old",
            "recent",
            "staffer",
        ]


_feed_seq = itertools.count()


def _feed(*, item=None, **kwargs):
    defaults = {
        "name": f"Users {next(_feed_seq)}",
        "context_model": "user",
        "order_by": "username",
        "page_size": 9,
    }
    defaults.update(kwargs)
    feed = Feed.objects.create(**defaults)
    feed.item = (
        item
        if item is not None
        else [
            {
                "type": "header",
                "value": {
                    "text": "{{ user.username }}",
                    "design": {},
                    "audience": {},
                },
            }
        ]
    )
    feed.save()
    return feed


class TestFeedRendering:
    def test_renders_items_and_paginates(self):
        USER_MODEL.objects.create(username="ada")
        USER_MODEL.objects.create(username="bob")
        data = render_feed(_feed(), RequestFactory().get("/"))
        assert "ada" in data["items_html"] and "bob" in data["items_html"]
        assert data["has_more"] is False and data["total"] == 2

        page = render_feed(_feed(page_size=1), RequestFactory().get("/"))
        assert page["has_more"] is True and page["next_offset"] == 1
        assert "ada" in page["items_html"] and "bob" not in page["items_html"]

    def test_builds_filters(self, settings):
        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
            "user": {
                "label": "User",
                "model": "auth.User",
                "filters": {
                    "active": {"type": "boolean", "field": "is_active"},
                    "tags": {
                        "type": "choice",
                        "multi": True,
                        "autocomplete": True,
                        "field": "username",
                        "choices": [("ada", "Ada")],
                    },
                    "sort": {
                        "label": "Sort",
                        "type": "sort",
                        "choices": [("username", "A-Z"), ("-username", "Z-A")],
                    },
                },
            }
        }
        reset_context_models()
        feed = _feed(order_by="username")
        feed.filters = [
            ("filter", {"key": "user:active"}),
            ("filter", {"key": "user:tags"}),
            ("filter", {"key": "user:sort"}),
        ]
        feed.save()
        data = render_feed(feed, RequestFactory().get("/"))
        by_key = {item["key"]: item for item in data["filters"]}
        assert by_key["active"]["type"] == "boolean"
        assert by_key["tags"]["autocomplete"] is True
        assert by_key["tags"]["multi"] is True
        assert by_key["sort"]["type"] == "sort"
        assert [option["value"] for option in by_key["sort"]["options"]] == [
            "username",
            "-username",
        ]

        USER_MODEL.objects.create(username="aaa")
        USER_MODEL.objects.create(username="zzz")
        ordered = render_feed(
            feed, RequestFactory().get("/", {"filter_sort": "-username"})
        )
        assert ordered["items_html"].index("zzz") < ordered["items_html"].index("aaa")

    def test_context_visibility_is_evaluated_per_item(self):
        USER_MODEL.objects.create(username="ada")
        USER_MODEL.objects.create(username="bob")
        feed = _feed(
            item=[
                {
                    "type": "header",
                    "value": {
                        "text": "ADA ONLY",
                        "design": {},
                        "audience": {},
                        "visibility": {
                            "switch_key": "",
                            "show_when": True,
                            "condition": {
                                "context_model": "user",
                                "field_name": "username",
                                "operator": "equals",
                                "compare_value": "ada",
                                "rule": "",
                                "invert": False,
                                "expression": "",
                            },
                        },
                    },
                }
            ]
        )
        html = render_feed(feed, RequestFactory().get("/"))["items_html"]
        assert html.count("ADA ONLY") == 1
        # Bob's item is present, but his conditional header is not rendered.
        assert html.count("data-daisie-feed-item") == 2

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
        data = render_feed(_feed(), RequestFactory().get("/"))
        assert "staffonly" in data["items_html"]
        assert "regularonly" not in data["items_html"]


class TestFeedEndpoint:
    def test_returns_items_fragment(self):
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
        html = feed_items(
            RequestFactory().get("/", {"block": "x"}), feed.pk
        ).content.decode()
        # The htmx slice carries the rendered items inside the swappable body.
        assert "ada" in html
        assert "daisie-feed__item" in html
        assert 'id="daisie-feed-body-x"' in html


class TestDateTransform:
    def test_date_and_datetime_fields(self):
        from django.db.models import DateField, DateTimeField

        from wagtail_daisIE.dynamic.feeds import _date_transform

        def config(field):
            class Meta:
                @staticmethod
                def get_field(name):
                    return field

            class Model:
                _meta = Meta

            return SimpleNamespace(model=Model)

        assert _date_transform(config(DateField()), "published") == "published"
        assert (
            _date_transform(config(DateTimeField()), "published") == "published__date"
        )
