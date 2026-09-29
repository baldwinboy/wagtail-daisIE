import json

import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import RequestFactory

from wagtail_daisIE.dynamic.mixins import DaisieContextMixin
from wagtail_daisIE.dynamic.registry import (
    get_context_model,
    get_context_model_choices,
    get_context_models,
    get_context_models_state,
    reset_context_models,
)
from wagtail_daisIE.dynamic.resolvers import (
    ContextBinding,
    resolve_binding,
    resolve_context_models,
    resolve_object,
    resolve_url_kwargs,
    url_for_object,
)
from wagtail_daisIE.dynamic.views import object_options


pytestmark = pytest.mark.django_db

USER_MODEL = get_user_model()

CONFIG = {
    "owner": {
        "label": "Owner",
        "model": "auth.User",
        "source": "request.user",
    },
    "target": {
        "label": "Target user",
        "model": "auth.User",
        "source": "url",
        "lookup_field": "pk",
    },
}


@pytest.fixture(autouse=True)
def _registry(settings):
    settings.WAGTAIL_DAISIE_CONTEXT_MODELS = CONFIG
    reset_context_models()
    yield
    reset_context_models()


def _request(user=None, kwargs=None, query=None, routes=None):
    request = RequestFactory().get("/", query or {})
    request.user = user
    request.resolver_match = type("Match", (), {"kwargs": kwargs or {}})()
    if routes is not None:
        request.routable_resolver_match = type("Match", (), {"kwargs": routes})()
    return request


def _binding(**kwargs):
    kwargs.setdefault("key", "target")
    kwargs.setdefault("mode", "url")
    return ContextBinding(**kwargs)


class TestRegistry:
    def test_returns_configured_models_and_choices(self, settings):
        models = get_context_models()
        assert set(models) == {"owner", "target"}
        assert models["owner"].model is USER_MODEL
        assert get_context_model_choices() == [
            ("owner", "Owner"),
            ("target", "Target user"),
        ]

        # Choices are built on demand, not cached at import time.
        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {}
        reset_context_models()
        assert get_context_model_choices() == []

    def test_state_marks_automatic_and_url(self, settings):
        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = CONFIG
        reset_context_models()
        state = get_context_models_state()
        assert state["owner"]["automatic"] is True
        assert state["owner"]["modes"] == ["automatic"]
        assert state["target"]["modes"] == ["url", "fixed"]
        assert state["target"]["fields"]


class TestResolution:
    def test_request_url_and_error_isolation(self):
        user = USER_MODEL.objects.create(username="ada")
        context = resolve_context_models(_request(user=user, kwargs={"pk": user.pk}))
        assert context["owner"] == user
        assert context["target"] == user

        assert resolve_context_models(_request(user=None))["owner"] is None

    def test_mixin_injects_into_context(self):
        user = USER_MODEL.objects.create(username="ada")
        request = _request(user=user)

        class Dummy(DaisieContextMixin):
            context_bindings = None

        assert Dummy().add_daisie_context(request, {})["owner"] == user
        # Existing values are never overwritten.
        assert Dummy().add_daisie_context(request, {"owner": "kept"})["owner"] == "kept"

    def test_resolve_object_dict_attr_and_filters(self):
        assert resolve_object("payload.title", {"payload": {"title": "Bread"}}) == (
            "Bread"
        )

        class Obj:
            name = "Meeting"

        assert resolve_object("meeting.name", {"meeting": Obj()}) == "Meeting"
        assert resolve_object("{{ payload.x|upper }}", {"payload": {"x": "a"}}) == "a"

    def test_url_for_object_variants(self):
        class WithAbsolute:
            def get_absolute_url(self):
                return "/detail/1/"

        class WithUrl:
            url = "https://example.com/x"

        assert url_for_object(WithAbsolute()) == "/detail/1/"
        assert url_for_object(WithUrl()) == "https://example.com/x"
        assert url_for_object("javascript:alert(1)") == ""
        assert url_for_object("/ok/") == "/ok/"

    def test_binding_fixed_and_fallback(self):
        user = USER_MODEL.objects.create(username="ada")
        config = get_context_model("owner")

        fixed = ContextBinding(key="owner", mode="fixed", object_id=user.pk)
        assert resolve_binding(config, fixed, _request()) == user
        missing = ContextBinding(key="owner", mode="fixed", object_id=999999)
        assert resolve_binding(config, missing, _request()) is None

        fallback = ContextBinding(key="owner", mode="automatic", fallback="Guest")
        assert resolve_binding(config, fallback, _request(user=None)) == "Guest"
        assert (
            resolve_binding(config, fallback, _request(user=AnonymousUser())) == "Guest"
        )

    def test_url_lookup_and_queryset_scoping(self, settings):
        user = USER_MODEL.objects.create(username="ada")
        request = _request(user=user, kwargs={"pk": user.pk}, query={"pk": user.pk})
        config = get_context_model("target")
        assert resolve_binding(config, _binding(lookup_in="path"), request) == user
        assert resolve_binding(config, _binding(lookup_in="query"), request) == user

        invalid = _request(query={"pk": "not-a-number"})
        assert resolve_binding(config, _binding(lookup_in="query"), invalid) is None
        pattern = _binding(lookup_in="query", lookup_pattern=r"\d+")
        assert resolve_binding(config, pattern, _request(query={"pk": "abc"})) is None

        # A lookup field the model does not have degrades to None, not an error.
        unknown = _binding(lookup_in="query", lookup_field="does_not_exist")
        assert (
            resolve_binding(config, unknown, _request(query={"does_not_exist": "x"}))
            is None
        )

        page = type("P", (), {"slug": "ada"})()
        assert resolve_url_kwargs(_request(), page=page) == {"slug": "ada"}

        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
            "target": {
                "label": "Target",
                "model": "auth.User",
                "source": "url",
                "lookup_field": "pk",
                "lookup_in": "query",
                "queryset": lambda request, page: USER_MODEL.objects.filter(
                    is_staff=True
                ),
            }
        }
        reset_context_models()
        staff = USER_MODEL.objects.create(username="staff", is_staff=True)
        scoped = _binding(lookup_in="query")
        assert (
            resolve_binding(
                get_context_model("target"), scoped, _request(query={"pk": staff.pk})
            )
            == staff
        )


class TestObjectOptionsEndpoint:
    def test_staff_and_model_guard_and_limit(self):
        staff = USER_MODEL.objects.create(username="staff", is_staff=True)
        USER_MODEL.objects.create(username="a")
        USER_MODEL.objects.create(username="b")
        request = _request(
            user=staff, query={"model": USER_MODEL._meta.label, "limit": "2"}
        )
        payload = json.loads(object_options(request).content)
        assert len(payload["results"]) == 2

        non_staff = _request(user=USER_MODEL.objects.create(username="anon"))
        with pytest.raises(Http404):
            object_options(non_staff)

        unconfigured = _request(user=staff, query={"model": "wagtailcore.Page"})
        with pytest.raises(Http404):
            object_options(unconfigured)
