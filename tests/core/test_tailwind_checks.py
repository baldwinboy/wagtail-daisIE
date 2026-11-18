from unittest.mock import patch

from django.contrib.staticfiles import finders
from django.test import override_settings

from wagtail_daisIE.checks import check_tailwind_compiler


MIDDLEWARE = ["wagtail_daisIE.middleware.TailwindCSSMiddleware"]


def _ids(warnings):
    return [warning.id for warning in warnings]


def test_no_warning_without_middleware():
    with override_settings(MIDDLEWARE=[]):
        assert check_tailwind_compiler(None) == []


@override_settings(
    MIDDLEWARE=MIDDLEWARE,
    TAILWIND_CSS_API={"url": "https://example.com/compile", "transport": "http"},
)
def test_valid_api_is_quiet(monkeypatch):
    monkeypatch.setattr(finders, "find", lambda path: True)
    assert _ids(check_tailwind_compiler(None)) == []


@override_settings(MIDDLEWARE=MIDDLEWARE, TAILWIND_CSS_API="")
def test_missing_compiler_warns(monkeypatch):
    monkeypatch.setattr(finders, "find", lambda path: True)
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    assert "wagtail_daisIE.W003" in _ids(check_tailwind_compiler(None))


@override_settings(
    MIDDLEWARE=MIDDLEWARE,
    TAILWIND_CSS_API="",
    TAILWIND_CLI_USE_DAISY_UI=False,
)
def test_daisyui_binary_warning(monkeypatch):
    monkeypatch.setattr(finders, "find", lambda path: True)
    assert "wagtail_daisIE.W004" in _ids(check_tailwind_compiler(None))


@override_settings(
    MIDDLEWARE=MIDDLEWARE,
    TAILWIND_CSS_API={"url": "https://example.com/compile", "transport": "websocket"},
)
def test_invalid_transport_warns(monkeypatch):
    monkeypatch.setattr(finders, "find", lambda path: True)
    assert "wagtail_daisIE.W006" in _ids(check_tailwind_compiler(None))


@override_settings(
    MIDDLEWARE=MIDDLEWARE,
    TAILWIND_CSS_API={
        "url": "wss://example.com/compile",
        "transport": "websocket",
        "token": "secret",
    },
)
def test_token_websocket_warns(monkeypatch):
    monkeypatch.setattr(finders, "find", lambda path: True)
    assert "wagtail_daisIE.W007" in _ids(check_tailwind_compiler(None))


@override_settings(
    MIDDLEWARE=MIDDLEWARE,
    TAILWIND_CSS_API={"url": "https://example.com/compile", "transport": "http"},
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "daisie-check",
        }
    },
)
def test_local_memory_cache_warns(monkeypatch):
    monkeypatch.setattr(finders, "find", lambda path: True)
    assert "wagtail_daisIE.W009" in _ids(check_tailwind_compiler(None))


@override_settings(
    MIDDLEWARE=MIDDLEWARE,
    TAILWIND_CSS_API={"url": "https://example.com/compile", "transport": "http"},
)
def test_missing_urls_warns(monkeypatch):
    monkeypatch.setattr(finders, "find", lambda path: True)
    from django.urls import NoReverseMatch

    with patch("django.urls.reverse", side_effect=NoReverseMatch):
        assert "wagtail_daisIE.W005" in _ids(check_tailwind_compiler(None))
