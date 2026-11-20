import itertools

from datetime import timedelta
from types import SimpleNamespace

import pytest

from django.contrib.auth import get_user_model
from django.http import HttpResponse, QueryDict
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils import timezone

from wagtail_daisIE.dynamic.actions import (
    get_action_choices,
    resolve_action,
    run_action,
)
from wagtail_daisIE.dynamic.feeds import (
    apply_filters,
    decode_layout_override,
    encode_layout_override,
    paginate_queryset,
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

    def test_event_content_does_not_inherit_calendar_design(self):
        now = timezone.now()
        USER_MODEL.objects.create(username="ada", date_joined=now)
        block = CalendarBlock()
        context = block.get_context(
            block.to_python(
                {
                    "context_model": "user",
                    "date_field": "date_joined",
                    "event": [
                        {
                            "type": "text",
                            "value": {
                                "text": "Event",
                                "design": {"typography": {"text_color": "text-accent"}},
                                "audience": {},
                            },
                        }
                    ],
                    "limit": 50,
                    "empty_message": "",
                    "design": {
                        "padding": {"all_padding": "p-8"},
                        "background": [
                            {
                                "type": "layer",
                                "value": {
                                    "layer_type": "solid",
                                    "color": "#ff0000",
                                },
                            }
                        ],
                    },
                    "audience": {},
                }
            )
        )
        assert "p-8" in context["block_css"].split()
        assert context["block_style"] == "background: #ff0000"

        event_html = "".join(context["days"][0]["events"])
        assert "text-accent" in event_html
        assert "p-8" not in event_html
        assert "background: #ff0000" not in event_html


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
        assert data["has_more"] is False and data["total"] is None

        page = render_feed(_feed(page_size=1), RequestFactory().get("/"))
        assert page["has_more"] is True and page["next_page_number"] == 2
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


class TestFeedLayoutAndState:
    def test_layout_toggle_requires_permission(self):
        feed = _feed(layout="grid", allow_layout_toggle=False)
        data = render_feed(feed, RequestFactory().get("/", {"layout": "list"}))
        assert data["layout"] == "grid"
        assert data["allow_layout_toggle"] is False

        enabled = _feed(layout="grid", allow_layout_toggle=True)
        data = render_feed(enabled, RequestFactory().get("/", {"layout": "list"}))
        assert data["layout"] == "list"

    def test_layout_toggle_active_css_is_exposed(self):
        feed = _feed()
        feed.layout_toggle_appearance = [
            (
                "appearance",
                {
                    "normal": {"color": "btn-primary"},
                    "hover": {},
                    "active": {"color": "btn-secondary"},
                },
            )
        ]
        feed.save()
        data = render_feed(feed, RequestFactory().get("/"))
        assert "btn-secondary" in data["layout_toggle_selected_css"]
        assert "active:btn-secondary" in data["layout_toggle_css"]

    def test_next_url_preserves_filters_and_adds_token(self):
        for username in ("a", "b", "c", "d"):
            USER_MODEL.objects.create(username=username)
        feed = _feed()
        data = render_feed(
            feed,
            RequestFactory().get(
                "/", {"filter_active": "1", "layout": "list", "limit": "3"}
            ),
            source_page=SimpleNamespace(pk=7),
            layout_token=encode_layout_override({"layout": "row"}),
        )
        next_url = data["next_url"]
        assert "filter_active=1" in next_url
        assert "layout=list" in next_url
        assert "limit=3" in next_url
        assert "page=2" in next_url
        assert "source_page=7" in next_url
        assert "layout_token=" in next_url
        assert "offset=" not in next_url

    def test_layout_token_round_trip_and_invalid(self):
        token = encode_layout_override({"layout": "list", "columns": 2})
        assert decode_layout_override(token) == {
            "layout": "list",
            "columns": 2,
        }
        assert decode_layout_override("not-a-token") == {}

    def test_filter_reset_url_preserves_other_state(self, settings):
        _filter_config(settings)
        feed = _feed(context_model="staff")
        feed.filters = [("filter", {"key": "staff:active"})]
        feed.save()
        data = render_feed(
            feed,
            RequestFactory().get("/", {"filter_active": "1", "layout": "list"}),
        )
        entry = data["filters"][0]
        assert "filter_active" not in entry["reset_url"]
        assert "layout=list" in entry["reset_url"]


class TestFeedTemplates:
    def test_filter_controls_carry_selected_state_attributes(self):
        html = render_to_string(
            "wagtail_daisIE/blocks/data/feed_filter.html",
            {
                "filter": {
                    "type": "choice",
                    "collapsed": False,
                    "container_css": "",
                    "label": "Tags",
                    "label_css": "",
                    "autocomplete": False,
                    "multi": False,
                    "key": "tags",
                    "options": [{"value": "a", "label": "A"}],
                    "values": ["a"],
                    "value": "a",
                    "button_css": "btn",
                    "selected_css": "",
                    "input_css": "",
                    "reset_url": "/feed?filter_other=1",
                }
            },
        )
        assert "data-daisie-selectable" in html
        assert 'data-daisie-selected-class=" btn-active"' in html
        assert 'href="/feed?filter_other=1"' in html

    def test_layout_and_load_more_attributes(self):
        form_html = render_to_string(
            "wagtail_daisIE/blocks/data/feed_filter_form.html",
            {
                "block": SimpleNamespace(id="feed-1"),
                "feed_url": "/feed/items/",
                "filters": [],
                "filter_menu": {"enabled": False},
                "filter_panel_css": "",
                "filter_layout_css": "",
                "allow_layout_toggle": True,
                "toggle_options": [{"value": "grid", "label": "Grid"}],
                "layout": "grid",
                "layout_toggle_css": "btn btn-sm",
                "layout_toggle_selected_css": "btn-primary",
                "layout_token": "token",
                "source_page_pk": "12",
                "submit_css": "btn",
            },
        )
        assert "data-daisie-selectable" in form_html
        assert "btn-primary" in form_html
        assert "feed_controls.js" in form_html
        assert "layout_token" in form_html

        body_html = render_to_string(
            "wagtail_daisIE/blocks/data/feed_body.html",
            {
                "block_id": "feed-1",
                "has_more": True,
                "has_previous": False,
                "previous_url": "",
                "next_url": "?page=2&filter_active=1",
                "next_page_number": 2,
                "feed_url": "/feed/items/",
                "infinite": True,
                "submit_css": "btn",
                "layout": "grid",
                "layout_container_css": "grid",
                "items_html": "",
                "total": 10,
                "empty_message": "",
            },
        )
        assert 'href="?page=2&amp;filter_active=1"' in body_html
        assert "revealed" in body_html
        assert 'data-daisie-feed-page="2"' in body_html


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

    def test_invalid_and_huge_query_values_do_not_raise(self):
        from wagtail_daisIE.dynamic.views import feed_items

        USER_MODEL.objects.create(username="ada")
        feed = _feed()
        for params in (
            {"page": "abc", "block": "x"},
            {"page": str(2**63), "block": "x"},
            {"limit": str(2**63), "block": "x"},
            {"offset": str(2**63), "block": "x"},
        ):
            response = feed_items(RequestFactory().get("/", params), feed.pk)
            assert response.status_code == 200

    def test_layout_token_applies_block_override(self):
        from wagtail_daisIE.dynamic.views import feed_items

        USER_MODEL.objects.create(username="ada")
        feed = _feed(layout="grid")
        token = encode_layout_override({"layout": "row"})
        html = feed_items(
            RequestFactory().get("/", {"layout_token": token, "block": "x"}),
            feed.pk,
        ).content.decode()
        assert "daisie-feed--row" in html

    def test_infinite_scroll_attribute_only_when_enabled(self):
        from wagtail_daisIE.dynamic.views import feed_items

        for index in range(3):
            USER_MODEL.objects.create(username=f"user{index}")
        finite = _feed(page_size=1, infinite=False)
        infinite = _feed(page_size=1, infinite=True)
        finite_html = feed_items(
            RequestFactory().get("/", {"block": "x"}), finite.pk
        ).content.decode()
        infinite_html = feed_items(
            RequestFactory().get("/", {"block": "x"}), infinite.pk
        ).content.decode()
        assert "revealed" not in finite_html
        assert "revealed" in infinite_html


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


class TestVisibilityScope:
    def test_feed_item_switch_scope(self):
        USER_MODEL.objects.create(username="ada")
        feed = _feed(
            item=[
                {
                    "type": "toggle",
                    "value": {
                        "label": "Toggle",
                        "logic_key": "notify",
                        "checked": True,
                        "design": {},
                        "audience": {},
                    },
                },
                {
                    "type": "header",
                    "value": {
                        "text": "Target",
                        "design": {},
                        "audience": {},
                        "visibility": {
                            "switch_key": "notify",
                            "show_when": True,
                            "condition": {},
                        },
                    },
                },
            ]
        )
        data = render_feed(feed, RequestFactory().get("/"))
        html = data["items_html"]
        assert 'data-daisie-switch-scope="feed-item"' in html
        assert "[data-daisie-feed-item]" in html
        assert 'data-daisie-visibility-key="notify"' in html

    def test_calendar_event_switch_scope(self):
        now = timezone.now()
        USER_MODEL.objects.create(username="ada", date_joined=now)
        block = CalendarBlock()
        context = block.get_context(
            block.to_python(
                {
                    "context_model": "user",
                    "date_field": "date_joined",
                    "event": [
                        {
                            "type": "toggle",
                            "value": {
                                "label": "Toggle",
                                "logic_key": "notify",
                                "checked": True,
                                "design": {},
                                "audience": {},
                            },
                        },
                        {
                            "type": "header",
                            "value": {
                                "text": "Target",
                                "design": {},
                                "audience": {},
                                "visibility": {
                                    "switch_key": "notify",
                                    "show_when": True,
                                    "condition": {},
                                },
                            },
                        },
                    ],
                    "limit": 50,
                    "empty_message": "",
                    "design": {},
                    "audience": {},
                }
            )
        )
        rendered = "".join(context["days"][0]["events"])
        assert 'data-daisie-switch-scope="calendar-event"' in rendered
        assert "[data-daisie-calendar-event]" in rendered


class TestFeedTitle:
    def test_title_optional_and_fallback(self):
        feed = Feed(name="internal", context_model="user")
        assert str(feed) == "internal"
        feed.title = "Friendly"
        assert str(feed) == "Friendly"
        feed.title = ""
        assert str(feed) == "internal"

    def test_duplicate_titles_are_allowed(self):
        first = Feed.objects.create(name="first", title="Same", context_model="user")
        second = Feed.objects.create(name="second", title="Same", context_model="user")
        assert str(first) == "Same"
        assert str(second) == "Same"

    def test_title_is_not_unique(self):
        field = Feed._meta.get_field("title")
        assert field.blank is True
        assert getattr(field, "unique", False) is False

    def test_name_remains_required_and_unique(self):
        field = Feed._meta.get_field("name")
        assert field.blank is False
        assert field.unique is True

    def test_viewset_search_and_list_display(self):
        from wagtail_daisIE.feeds.view_sets import FeedViewSet

        assert "title" in FeedViewSet.list_display
        assert "name" in FeedViewSet.list_display
        assert FeedViewSet.search_fields == ["title", "name"]


class TestCountlessPagination:
    def test_countless_page_makes_no_count_query(self, django_assert_num_queries):
        for username in ("ada", "bob", "cy"):
            USER_MODEL.objects.create(username=username)
        with django_assert_num_queries(1):
            page_obj, total = paginate_queryset(
                USER_MODEL.objects.order_by("username"), 2, 1
            )
        assert [user.username for user in page_obj] == ["ada", "bob"]
        assert page_obj.has_next() is True
        assert page_obj.next_page_number() == 2
        assert total is None

    def test_second_page_has_previous_and_no_next(self):
        for username in ("ada", "bob", "cy"):
            USER_MODEL.objects.create(username=username)
        page_obj, _ = paginate_queryset(USER_MODEL.objects.order_by("username"), 2, 2)
        assert [user.username for user in page_obj] == ["cy"]
        assert page_obj.has_previous() is True
        assert page_obj.has_next() is False
        assert page_obj.previous_page_number() == 1

    def test_invalid_page_values_fall_back_to_page_one(self):
        USER_MODEL.objects.create(username="ada")
        page_obj, _ = paginate_queryset(
            USER_MODEL.objects.order_by("username"), 2, "abc"
        )
        assert page_obj.number == 1
        assert [user.username for user in page_obj] == ["ada"]

    def test_empty_page_is_safe(self):
        USER_MODEL.objects.create(username="ada")
        page_obj, _ = paginate_queryset(USER_MODEL.objects.order_by("username"), 2, 99)
        assert list(page_obj) == []
        assert page_obj.has_next() is False

    def test_stock_fallback_performs_one_count_query(self, monkeypatch):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        def reject(*args, **kwargs):
            raise TypeError("rejected")

        monkeypatch.setattr("wagtail_daisIE.dynamic.feeds.CountlessPaginator", reject)
        USER_MODEL.objects.create(username="ada")
        with CaptureQueriesContext(connection) as context:
            page_obj, total = paginate_queryset(
                USER_MODEL.objects.order_by("username"), 2, 1
            )
        counts = [
            query["sql"]
            for query in context.captured_queries
            if "COUNT(" in query["sql"].upper()
        ]
        assert len(counts) == 1
        assert total == 1
        assert [user.username for user in page_obj] == ["ada"]


class TestFeedPagination:
    def test_page_links_and_previous(self):
        for username in ("user-a", "user-b", "user-c", "user-d", "user-e"):
            USER_MODEL.objects.create(username=username)
        data = render_feed(_feed(page_size=2), RequestFactory().get("/", {"page": "2"}))
        assert data["page_number"] == 2
        assert data["has_previous"] is True
        assert "page=1" in data["previous_url"]
        assert data["has_more"] is True
        assert "page=3" in data["next_url"]
        assert ">user-a<" not in data["items_html"]
        assert ">user-c<" in data["items_html"]

    def test_invalid_and_huge_pages_are_safe(self):
        USER_MODEL.objects.create(username="ada")
        for params in ({"page": "abc"}, {"page": "0"}):
            data = render_feed(_feed(), RequestFactory().get("/", params))
            assert ">ada<" in data["items_html"]
            assert data["has_more"] is False

        huge = render_feed(_feed(), RequestFactory().get("/", {"page": str(2**63)}))
        assert huge["items_html"] == ""
        assert huge["has_more"] is False

    def test_legacy_limit_and_offset_aliases(self):
        for username in ("user-a", "user-b", "user-c", "user-d"):
            USER_MODEL.objects.create(username=username)
        limit_data = render_feed(
            _feed(page_size=2), RequestFactory().get("/", {"limit": "2"})
        )
        assert ">user-a<" in limit_data["items_html"]
        assert ">user-c<" not in limit_data["items_html"]
        assert (
            "page=2" in limit_data["next_url"] and "limit=2" in limit_data["next_url"]
        )

        offset_data = render_feed(
            _feed(page_size=2), RequestFactory().get("/", {"offset": "2"})
        )
        assert ">user-c<" in offset_data["items_html"]

    def test_total_policy_and_source_page(self):
        USER_MODEL.objects.create(username="ada")
        data = render_feed(
            _feed(), RequestFactory().get("/"), source_page=SimpleNamespace(pk=7)
        )
        assert data["total"] is None
        assert "source_page=7" in data["next_url"]

    def test_repeated_page_requests_are_idempotent(self):
        USER_MODEL.objects.create(username="ada")
        first = render_feed(_feed(), RequestFactory().get("/", {"page": "1"}))
        second = render_feed(_feed(), RequestFactory().get("/", {"page": "1"}))
        assert first["items_html"] == second["items_html"]


class TestFeedPaginationTemplates:
    def test_total_policy_in_body(self):
        without_total = render_to_string(
            "wagtail_daisIE/blocks/data/feed_body.html",
            {
                "block_id": "feed-1",
                "has_more": False,
                "has_previous": False,
                "previous_url": "",
                "next_url": "",
                "next_page_number": 1,
                "feed_url": "/feed/items/",
                "layout": "grid",
                "layout_container_css": "grid",
                "items_html": "",
                "total": None,
                "empty_message": "",
            },
        )
        with_total = render_to_string(
            "wagtail_daisIE/blocks/data/feed_body.html",
            {
                "block_id": "feed-1",
                "has_more": False,
                "has_previous": False,
                "previous_url": "",
                "next_url": "",
                "next_page_number": 1,
                "feed_url": "/feed/items/",
                "layout": "grid",
                "layout_container_css": "grid",
                "items_html": "",
                "total": 10,
                "empty_message": "",
            },
        )
        assert "data-daisie-feed-total" not in without_total
        assert 'data-daisie-feed-total="10"' in with_total

    def test_append_fragment_shape(self):
        html = render_to_string(
            "wagtail_daisIE/blocks/data/feed_items.html",
            {
                "block_id": "feed-1",
                "has_more": True,
                "has_previous": True,
                "previous_url": "?page=1",
                "next_url": "?page=3",
                "next_page_number": 3,
                "feed_url": "/feed/items/",
                "items_html": '<div class="daisie-feed__item">ada</div>',
                "submit_css": "btn",
                "hide_previous": True,
                "oob": True,
            },
        )
        assert "ada" in html
        assert "hx-swap-oob" in html
        assert "hidden" in html
        assert 'id="daisie-feed-body-feed-1"' not in html


class TestFeedPaginationEndpoint:
    def test_items_fragment(self):
        from wagtail_daisIE.dynamic.views import feed_items

        USER_MODEL.objects.create(username="ada")
        USER_MODEL.objects.create(username="bob")
        feed = _feed(page_size=1)
        html = feed_items(
            RequestFactory().get("/", {"block": "x", "page": "2", "fragment": "items"}),
            feed.pk,
        ).content.decode()
        assert "bob" in html
        assert "ada" not in html
        assert "hx-swap-oob" in html
        assert 'id="daisie-feed-body-x"' not in html

    def test_filter_form_has_no_page_or_offset(self):
        html = render_to_string(
            "wagtail_daisIE/blocks/data/feed_filter_form.html",
            {
                "block": SimpleNamespace(id="feed-1"),
                "feed_url": "/feed/items/",
                "filters": [],
                "filter_menu": {"enabled": False},
                "filter_panel_css": "",
                "filter_layout_css": "",
                "allow_layout_toggle": False,
                "toggle_options": [],
                "layout": "grid",
                "layout_toggle_css": "btn btn-sm",
                "layout_toggle_selected_css": "btn-primary",
                "layout_token": "token",
                "source_page_pk": "12",
                "submit_css": "btn",
            },
        )
        assert 'name="page"' not in html
        assert 'name="offset"' not in html
        assert "source_page" in html


class TestFilterChoiceLimits:
    def _config(self, settings, *, autocomplete=False, choice_limit=None):
        def choices(request, page):
            return [
                {"value": str(index), "label": f"Option {index}"}
                for index in range(150)
            ]

        spec = {
            "type": "choice",
            "multi": True,
            "field": "username",
            "choices": choices,
        }
        if autocomplete:
            spec["autocomplete"] = True
        if choice_limit is not None:
            spec["choice_limit"] = choice_limit
        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
            "user": {"label": "User", "model": "auth.User", "filters": {"tags": spec}}
        }
        reset_context_models()
        return get_context_model("user")

    def _feed_with_filter(self, feed):
        feed.filters = [("filter", {"key": "user:tags"})]
        feed.save()
        return feed

    def test_default_choice_limit(self, settings):
        self._config(settings)
        feed = self._feed_with_filter(_feed())
        data = render_feed(feed, RequestFactory().get("/"))
        assert len(data["filters"][0]["options"]) == 100

    def test_autocomplete_default_limit(self, settings):
        self._config(settings, autocomplete=True)
        feed = self._feed_with_filter(_feed())
        data = render_feed(feed, RequestFactory().get("/"))
        entry = data["filters"][0]
        assert len(entry["options"]) == 20
        assert entry["remote_url"]

    def test_custom_choice_limit(self, settings):
        self._config(settings, choice_limit=5)
        feed = self._feed_with_filter(_feed())
        data = render_feed(feed, RequestFactory().get("/"))
        assert len(data["filters"][0]["options"]) == 5

    def test_selected_value_beyond_limit_is_retained(self, settings):
        self._config(settings)
        feed = self._feed_with_filter(_feed())
        data = render_feed(feed, RequestFactory().get("/", {"filter_tags": "149"}))
        options = data["filters"][0]["options"]
        assert any(
            option["value"] == "149" and option["label"] == "Option 149"
            for option in options
        )

    def test_unknown_selected_value_gets_raw_label(self, settings):
        self._config(settings)
        feed = self._feed_with_filter(_feed())
        data = render_feed(feed, RequestFactory().get("/", {"filter_tags": "missing"}))
        options = data["filters"][0]["options"]
        assert any(
            option["value"] == "missing" and option["label"] == "missing"
            for option in options
        )

    def test_short_autocomplete_has_no_remote_url(self, settings):
        def choices(request, page):
            return [{"value": "1", "label": "One"}]

        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
            "user": {
                "label": "User",
                "model": "auth.User",
                "filters": {
                    "tags": {
                        "type": "choice",
                        "multi": True,
                        "autocomplete": True,
                        "field": "username",
                        "choices": choices,
                    }
                },
            }
        }
        reset_context_models()
        feed = _feed()
        feed.filters = [("filter", {"key": "user:tags"})]
        feed.save()
        data = render_feed(feed, RequestFactory().get("/"))
        assert not data["filters"][0]["remote_url"]


class TestFilterResolution:
    def test_choices_resolved_once(self, settings):
        calls = {"count": 0}

        def choices(request, page):
            calls["count"] += 1
            return [("a", "A"), ("b", "B")]

        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
            "user": {
                "label": "User",
                "model": "auth.User",
                "filters": {
                    "sort": {
                        "type": "sort",
                        "field": "username",
                        "choices": choices,
                    }
                },
            }
        }
        reset_context_models()
        feed = _feed()
        feed.filters = [("filter", {"key": "user:sort"})]
        feed.save()
        render_feed(feed, RequestFactory().get("/"))
        assert calls["count"] == 1

    def test_filter_menu_resolved_once(self, settings, monkeypatch):
        import wagtail_daisIE.dynamic.feeds as feeds

        original = feeds.build_filter_menu
        calls = {"count": 0}

        def counted(feed):
            calls["count"] += 1
            return original(feed)

        monkeypatch.setattr(feeds, "build_filter_menu", counted)
        feed = _feed()
        render_feed(feed, RequestFactory().get("/"))
        assert calls["count"] == 1


class TestFeedFilterChoicesEndpoint:
    def test_returns_filtered_results(self):
        from wagtail_daisIE.dynamic.views import feed_filter_choices

        def choices(request, page):
            return [
                {"value": str(index), "label": f"Option {index}"} for index in range(5)
            ]

        from django.test import override_settings

        with override_settings(
            WAGTAIL_DAISIE_CONTEXT_MODELS={
                "user": {
                    "label": "User",
                    "model": "auth.User",
                    "filters": {
                        "tags": {
                            "type": "choice",
                            "multi": True,
                            "autocomplete": True,
                            "field": "username",
                            "choices": choices,
                        }
                    },
                }
            }
        ):
            reset_context_models()
            feed = _feed()
            feed.filters = [("filter", {"key": "user:tags"})]
            feed.save()
            response = feed_filter_choices(
                RequestFactory().get("/", {"q": "Option 2"}), feed.pk, "tags"
            )
            assert response.status_code == 200
            import json

            payload = json.loads(response.content)
            assert [item["value"] for item in payload["results"]] == ["2"]

    def test_unknown_feed_or_filter_returns_404(self):
        from django.http import Http404

        from wagtail_daisIE.dynamic.views import feed_filter_choices

        feed = _feed()
        with pytest.raises(Http404):
            feed_filter_choices(RequestFactory().get("/"), 999999, "tags")
        with pytest.raises(Http404):
            feed_filter_choices(RequestFactory().get("/"), feed.pk, "missing")


class TestFilterAutocompleteTemplate:
    def test_remote_url_emitted(self):
        html = render_to_string(
            "wagtail_daisIE/blocks/data/feed_filter.html",
            {
                "filter": {
                    "type": "choice",
                    "autocomplete": True,
                    "label": "Tags",
                    "key": "tags",
                    "options": [{"value": "1", "label": "One"}],
                    "values": [],
                    "remote_url": "/daisie/feeds/1/filter/tags/choices/?source_page=7",
                    "input_css": "",
                    "container_css": "",
                    "label_css": "",
                    "button_css": "btn",
                    "selected_css": "",
                    "reset_url": "/",
                    "collapsed": False,
                }
            },
        )
        assert "data-daisyui-autocomplete-url" in html


class TestFeedQueryBudget:
    def _count(self, func):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as context:
            func()
        return len(context.captured_queries)

    def _request(self, page="1", active=None):
        params = {"page": page}
        if active is not None:
            params["filter_active"] = str(active)
        return RequestFactory().get("/", params)

    def test_append_and_filter_costs_do_not_grow(self):
        for index in range(12):
            USER_MODEL.objects.create(
                username=f"user-{index:02d}", is_active=index % 2 == 0
            )

        from django.test import override_settings

        with override_settings(
            WAGTAIL_DAISIE_CONTEXT_MODELS={
                "user": {
                    "label": "User",
                    "model": "auth.User",
                    "filters": {
                        "active": {"type": "boolean", "field": "is_active"},
                    },
                }
            }
        ):
            reset_context_models()
            feed = _feed(page_size=3)
            feed.filters = [("filter", {"key": "user:active"})]
            feed.save()

            initial = self._count(lambda: render_feed(feed, self._request("1")))
            append = self._count(lambda: render_feed(feed, self._request("2")))
            filtered = self._count(
                lambda: render_feed(feed, self._request("1", active="1"))
            )
            later_append = self._count(lambda: render_feed(feed, self._request("3")))

            assert append <= initial
            assert filtered <= initial
            assert later_append == append

    def test_append_does_not_repeat_page_one_cost_growth(self):
        for index in range(12):
            USER_MODEL.objects.create(username=f"user-{index:02d}")

        feed = _feed(page_size=3)
        first = self._count(lambda: render_feed(feed, self._request("1")))
        second = self._count(lambda: render_feed(feed, self._request("2")))
        third = self._count(lambda: render_feed(feed, self._request("3")))
        assert second == first
        assert third == first

    def test_item_relation_is_prefetched(self):
        from django.contrib.auth.models import Group

        group = Group.objects.create(name="admins")
        for index in range(4):
            user = USER_MODEL.objects.create(username=f"user-{index}")
            user.groups.add(group)

        from django.test import override_settings

        with override_settings(
            WAGTAIL_DAISIE_CONTEXT_MODELS={
                "user": {
                    "label": "User",
                    "model": "auth.User",
                    "prefetch_related": ["groups"],
                }
            }
        ):
            reset_context_models()
            feed = _feed(page_size=4)
            feed.item = [
                {
                    "type": "header",
                    "value": {
                        "text": "{{ user.groups }}",
                        "design": {},
                        "audience": {},
                    },
                }
            ]
            feed.save()

            from django.db import connection
            from django.test.utils import CaptureQueriesContext

            with CaptureQueriesContext(connection) as context:
                data = render_feed(feed, RequestFactory().get("/"))
            assert "admins" in data["items_html"]

            group_queries = [
                query["sql"]
                for query in context.captured_queries
                if "auth_user_groups" in query["sql"].lower()
                or "auth_group" in query["sql"].lower()
            ]
            assert len(group_queries) <= 2

            with CaptureQueriesContext(connection) as second:
                render_feed(feed, RequestFactory().get("/"))
            second_group_queries = [
                query["sql"]
                for query in second.captured_queries
                if "auth_user_groups" in query["sql"].lower()
                or "auth_group" in query["sql"].lower()
            ]
            assert len(second_group_queries) == len(group_queries)
