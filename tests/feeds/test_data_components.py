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
    LAYOUT_CHOICES,
    TOGGLE_PAIRS,
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


def _feed(**kwargs):
    defaults = {
        "name": f"Users {next(_feed_seq)}",
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


class TestFilterStyling:
    def test_filter_and_submit_css(self, settings):
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
        data = render_feed(feed, RequestFactory().get("/"))
        by_key = {item["key"]: item for item in data["filters"]}
        assert "btn-primary" in by_key["active"]["button_css"]
        assert "btn-secondary" in by_key["active"]["selected_css"]
        assert "font-bold" in by_key["active"]["label_css"]
        assert "text-sm" in by_key["joined"]["input_css"]
        assert "btn-secondary" in data["submit_css"]


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


_feed_seq = itertools.count()


class TestFeedLayout:
    def _feed(self, **kwargs):
        kwargs.setdefault("name", f"layout {next(_feed_seq)}")
        defaults = {"context_model": "user", "order_by": "username"}
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

    def _render(self, **kwargs):
        return render_feed(self._feed(**kwargs), RequestFactory().get("/"))

    def test_container_classes_and_clamping(self):
        grid = self._render(layout="grid", layout_columns=4, layout_gap="gap-6")[
            "layout_container_css"
        ].split()
        assert {"grid", "lg:grid-cols-4", "gap-6", "daisie-feed--grid"} <= set(grid)
        scroll = self._render(layout="row", row_mode="scroll")[
            "layout_container_css"
        ].split()
        assert {"flex-nowrap", "overflow-x-auto", "daisie-feed--row-scroll"} <= set(
            scroll
        )
        assert (
            "lg:grid-cols-3"
            in self._render(layout="grid", layout_columns=99)["layout_container_css"]
        )

    def test_block_override_and_query_override(self):
        from wagtail_daisIE.dynamic.feeds import resolve_layout

        feed = self._feed(layout="grid", layout_columns=2)
        ctx = resolve_layout(feed, {"layout": "list", "columns": 5}, None)
        assert ctx["layout"] == "list"
        assert "lg:grid-cols-5" in ctx["layout_classes"]["grid"]

        feed = self._feed(
            layout="grid", allow_layout_toggle=True, toggle_layouts="grid_row"
        )
        assert [
            o["value"] for o in resolve_layout(feed, None, None)["toggle_options"]
        ] == [
            "grid",
            "row",
        ]
        assert (
            resolve_layout(feed, None, RequestFactory().get("/?layout=row"))["layout"]
            == "row"
        )
        # ``list`` is not one of this feed's toggle options, so it is ignored.
        assert (
            resolve_layout(feed, None, RequestFactory().get("/?layout=list"))["layout"]
            == "grid"
        )
        assert (
            resolve_layout(feed, None, RequestFactory().get("/?layout=bogus"))["layout"]
            == "grid"
        )

    def test_template_renders_toggle_and_container(self):
        from wagtail_daisIE.feeds.blocks_data import FeedBlock

        block = FeedBlock()
        value = block.to_python(
            {
                "feed": self._feed(
                    allow_layout_toggle=True, toggle_layouts="grid_list"
                ).pk,
                "design": {},
                "audience": {},
            }
        )
        html = block.render(value, context={"request": RequestFactory().get("/")})
        # The layout toggle is a set of htmx-driven radio inputs on the form.
        assert 'name="layout"' in html
        assert "hx-get=" in html
        assert 'id="daisie-feed-body-' in html
        assert "daisie-feed--grid" in html
        assert html.count("btn-active") == 1

        listed = render_feed(self._feed(layout="list"), RequestFactory().get("/"))
        assert (
            "divide-y divide-base-300 daisie-feed--list"
            in listed["layout_container_css"]
        )

    def test_choices_are_shared_by_model_and_override_block(self):
        from wagtail_daisIE.dynamic import feeds
        from wagtail_daisIE.feeds.blocks_data import (
            LAYOUT_OVERRIDE_CHOICES,
            TOGGLE_OVERRIDE_CHOICES,
        )

        layouts = {key for key, _label in LAYOUT_CHOICES}
        for pair in TOGGLE_PAIRS.values():
            assert set(pair) <= layouts, pair
        assert [(k, str(v)) for k, v in LAYOUT_CHOICES] == [
            (k, str(v))
            for k, v in Feed.objects.none().model._meta.get_field("layout").choices
        ]
        assert LAYOUT_OVERRIDE_CHOICES[0][0] == ""
        assert TOGGLE_OVERRIDE_CHOICES[1:] == [
            (k, str(v)) for k, v in feeds.TOGGLE_CHOICES
        ]
