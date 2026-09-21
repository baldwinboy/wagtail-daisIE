import json

import pytest

from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import RequestFactory

from wagtail_daisIE.dynamic.registry import (
    get_context_model,
    get_context_model_choices,
    get_context_models,
    reset_context_models,
)
from wagtail_daisIE.dynamic.resolvers import (
    ContextBinding,
    resolve_context_models,
    resolve_object,
    sanitize_url,
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


class TestRegistry:
    def test_returns_configured_models(self):
        models = get_context_models()
        assert set(models) == {"owner", "target"}
        assert models["owner"].model is USER_MODEL

    def test_choices_are_lazy(self):
        choices = get_context_model_choices()
        assert ("owner", "Owner") in choices

    def test_unknown_model_resolves_to_none(self, settings):
        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
            "broken": {"label": "Broken", "model": "does.not.Exist"}
        }
        reset_context_models()
        assert get_context_model("broken").model is None

    def test_empty_config(self, settings):
        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {}
        reset_context_models()
        assert get_context_models() == {}


class TestResolution:
    def _request(self, user=None, kwargs=None):
        request = RequestFactory().get("/")
        request.user = user
        request.resolver_match = type("Match", (), {"kwargs": kwargs or {}})()
        return request

    def test_request_source(self):
        user = USER_MODEL.objects.create(username="ada")
        context = resolve_context_models(self._request(user=user))
        assert context["owner"] == user
        assert context["target"] is None

    def test_url_source(self):
        user = USER_MODEL.objects.create(username="ada")
        context = resolve_context_models(
            self._request(user=user, kwargs={"pk": user.pk})
        )
        assert context["target"] == user

    def test_source_errors_are_isolated(self):
        context = resolve_context_models(self._request(user=None))
        assert context["owner"] is None

    def test_mixin_injects_into_context(self):
        from wagtail_daisIE.dynamic.mixins import DaisieContextMixin

        user = USER_MODEL.objects.create(username="ada")
        request = self._request(user=user)

        class Dummy(DaisieContextMixin):
            context_bindings = None

        context = Dummy().add_daisie_context(request, {})
        assert context["owner"] == user
        # Existing values are never overwritten.
        context = Dummy().add_daisie_context(request, {"owner": "kept"})
        assert context["owner"] == "kept"


class TestResolveObject:
    def test_dict_lookup(self):
        assert resolve_object("payload.title", {"payload": {"title": "Bread"}}) == (
            "Bread"
        )

    def test_attribute_lookup(self):
        class Obj:
            name = "Meeting"

        assert resolve_object("meeting.name", {"meeting": Obj()}) == "Meeting"

    def test_braces_and_filters_are_stripped(self):
        assert resolve_object("{{ payload.x|upper }}", {"payload": {"x": "a"}}) == "a"

    def test_missing_root(self):
        assert resolve_object("missing.x", {}) is None


class TestSanitizeUrl:
    def test_relative_and_http_allowed(self):
        assert sanitize_url("/page/") == "/page/"
        assert sanitize_url("https://example.com") == "https://example.com"

    def test_mailto_and_tel_allowed(self):
        assert sanitize_url("mailto:a@b.com") == "mailto:a@b.com"
        assert sanitize_url("tel:123") == "tel:123"

    def test_dangerous_scheme_blocked(self):
        assert sanitize_url("javascript:alert(1)") == ""
        assert sanitize_url("data:text/html,x") == ""

    def test_none(self):
        assert sanitize_url(None) == ""


class TestUrlForObject:
    def test_get_absolute_url(self):
        class Obj:
            def get_absolute_url(self):
                return "/detail/1/"

        assert url_for_object(Obj()) == "/detail/1/"

    def test_url_attribute(self):
        class Obj:
            url = "https://example.com/x"

        assert url_for_object(Obj()) == "https://example.com/x"

    def test_string_is_sanitized(self):
        assert url_for_object("javascript:alert(1)") == ""
        assert url_for_object("/ok/") == "/ok/"


class TestBindingResolution:
    def _request(self, user=None):
        request = RequestFactory().get("/")
        request.user = user
        request.resolver_match = type("Match", (), {"kwargs": {}})()
        return request

    def test_fixed_binding(self):
        user = USER_MODEL.objects.create(username="ada")
        binding = ContextBinding(key="owner", mode="fixed", object_id=user.pk)
        config = get_context_model("owner")

        from wagtail_daisIE.dynamic.resolvers import resolve_binding

        assert resolve_binding(config, binding, self._request()) == user

    def test_fixed_binding_missing_object(self):
        binding = ContextBinding(key="owner", mode="fixed", object_id=999999)
        config = get_context_model("owner")

        from wagtail_daisIE.dynamic.resolvers import resolve_binding

        assert resolve_binding(config, binding, self._request()) is None

    def test_fallback_for_missing_value(self):
        binding = ContextBinding(key="owner", mode="automatic", fallback="Guest")
        config = get_context_model("owner")

        from wagtail_daisIE.dynamic.resolvers import resolve_binding

        assert resolve_binding(config, binding, self._request(user=None)) == "Guest"

    def test_fallback_for_anonymous_user(self):
        from django.contrib.auth.models import AnonymousUser

        binding = ContextBinding(key="owner", mode="automatic", fallback="Guest")
        config = get_context_model("owner")

        from wagtail_daisIE.dynamic.resolvers import resolve_binding

        request = self._request(user=AnonymousUser())
        assert resolve_binding(config, binding, request) == "Guest"


class TestRegistryState:
    def test_state_marks_automatic_and_url(self, settings):
        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
            "user": {"label": "User", "model": "auth.User", "source": "request.user"},
            "post": {
                "label": "Post",
                "model": "auth.User",
                "source": "url",
                "lookup_field": "pk",
            },
        }
        reset_context_models()

        from wagtail_daisIE.dynamic.registry import get_context_models_state

        state = get_context_models_state()
        assert state["user"]["automatic"] is True
        assert state["user"]["modes"] == ["automatic"]
        assert state["post"]["automatic"] is False
        assert state["post"]["modes"] == ["url", "fixed"]
        assert state["post"]["fields"]


class TestObjectOptionsEndpoint:
    def test_requires_staff(self):
        request = RequestFactory().get("/admin/wagtail_daisIE/dynamic/objects/")
        request.user = USER_MODEL.objects.create(username="anon")
        with pytest.raises(Http404):
            object_options(request)

    def test_returns_options_for_allowed_model(self):
        staff = USER_MODEL.objects.create(username="staff", is_staff=True)
        USER_MODEL.objects.create(username="ada")
        request = RequestFactory().get(
            "/admin/wagtail_daisIE/dynamic/objects/",
            {"model": USER_MODEL._meta.label},
        )
        request.user = staff
        response = object_options(request)
        payload = json.loads(response.content)
        assert any(item["text"] for item in payload["results"])

    def test_rejects_unconfigured_model(self):
        staff = USER_MODEL.objects.create(username="staff", is_staff=True)
        request = RequestFactory().get(
            "/admin/wagtail_daisIE/dynamic/objects/",
            {"model": "wagtailcore.Page"},
        )
        request.user = staff
        with pytest.raises(Http404):
            object_options(request)

    def test_respects_limit(self):
        staff = USER_MODEL.objects.create(username="staff", is_staff=True)
        USER_MODEL.objects.create(username="a")
        USER_MODEL.objects.create(username="b")
        request = RequestFactory().get(
            "/admin/wagtail_daisIE/dynamic/objects/",
            {"model": USER_MODEL._meta.label, "limit": "2"},
        )
        request.user = staff
        payload = json.loads(object_options(request).content)
        assert len(payload["results"]) == 2


class TestContextQueryset:
    def test_queryset_callable(self, settings):
        staff = USER_MODEL.objects.create(username="staffonly", is_staff=True)
        USER_MODEL.objects.create(username="regularonly")
        settings.WAGTAIL_DAISIE_CONTEXT_MODELS = {
            "staff": {
                "label": "Staff",
                "model": "auth.User",
                "queryset": lambda request, page: USER_MODEL.objects.filter(
                    is_staff=True
                ),
            }
        }
        reset_context_models()

        from wagtail_daisIE.dynamic.registry import get_context_model

        config = get_context_model("staff")
        assert list(config.get_queryset(None, None)) == [staff]

    def test_no_queryset_returns_none(self):
        from wagtail_daisIE.dynamic.registry import get_context_model

        config = get_context_model("owner")
        assert config.get_queryset(None, None) is None
