import json
import re

import pytest

from django.test import RequestFactory, override_settings

from wagtail_daisIE.tailwindcss import artifacts, orchestration
from wagtail_daisIE.tailwindcss.api import TailwindAPI


pytestmark = pytest.mark.django_db

TOKEN = "a" * 64


def _html(fragment=False):
    if fragment:
        return '<div class="flex"></div>'
    return (
        "<html><head>"
        '<script id="daisyui-jit-config" type="application/json">{}</script>'
        '</head><body class="flex"></body></html>'
    )


def _request(asgi=False):
    request = RequestFactory().get("/")
    if asgi:
        request.scope = {}
    return request


def _config(html):
    match = re.search(
        r'<script id="daisyui-jit-config[^"]*" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    assert match
    return json.loads(match.group(1))


def _patches(monkeypatch, *, output=None, api=None, celery=False):
    calls = {"blocking": 0, "http": 0, "celery": 0, "submit": 0}
    monkeypatch.setattr(artifacts, "store_input", lambda css: TOKEN)
    monkeypatch.setattr(artifacts, "get_output", lambda token: output)
    monkeypatch.setattr(artifacts, "output_url", lambda token: "/out.css")
    monkeypatch.setattr(artifacts, "input_url", lambda token: "/in.css")
    monkeypatch.setattr(
        orchestration,
        "_compile_and_store",
        lambda *args: calls.__setitem__("blocking", calls["blocking"] + 1),
    )
    monkeypatch.setattr(
        orchestration,
        "_compile_http_and_store",
        lambda *args: calls.__setitem__("http", calls["http"] + 1),
    )
    monkeypatch.setattr(
        orchestration,
        "_dispatch_celery",
        lambda token: (calls.__setitem__("celery", calls["celery"] + 1), celery)[1],
    )
    monkeypatch.setattr(
        orchestration,
        "_submit",
        lambda *args: (calls.__setitem__("submit", calls["submit"] + 1), True)[1],
    )
    monkeypatch.setattr(orchestration, "_celery_available", lambda: celery)
    monkeypatch.setattr(orchestration, "get_tailwind_api", lambda: api)
    return calls


def _http_api(token=""):
    return TailwindAPI(
        url="https://example.com/compile",
        transport="http",
        token=token,
        timeout=30,
    )


def _ws_api(token=""):
    return TailwindAPI(
        url="wss://example.com/compile",
        transport="websocket",
        token=token,
        timeout=30,
    )


def test_wsgi_no_api_no_celery_blocks(monkeypatch):
    calls = _patches(monkeypatch)
    config = _config(orchestration.prepare_html(_request(), _html(), fragment=False))
    assert config["mode"] == "fetch"
    assert "nonce" not in config
    assert calls == {"blocking": 1, "http": 0, "celery": 0, "submit": 0}


def test_wsgi_http_api_is_handled_by_js(monkeypatch):
    calls = _patches(monkeypatch, api=_http_api())
    config = _config(orchestration.prepare_html(_request(), _html(), fragment=False))
    assert config["mode"] == "http"
    assert config["api"]["transport"] == "http"
    assert config["api"]["url"].startswith("https://example.com/compile?nonce=")
    assert "nonce" not in config
    assert calls["blocking"] == 0


def test_wsgi_websocket_api_is_handled_by_js(monkeypatch):
    calls = _patches(monkeypatch, api=_ws_api())
    config = _config(orchestration.prepare_html(_request(), _html(), fragment=False))
    assert config["mode"] == "ws"
    assert config["api"]["transport"] == "websocket"
    assert config["api"]["url"].startswith("wss://example.com/compile?nonce=")
    assert "nonce" not in config
    assert calls["blocking"] == 0


def test_wsgi_celery_no_api(monkeypatch):
    calls = _patches(monkeypatch, celery=True)
    config = _config(orchestration.prepare_html(_request(), _html(), fragment=False))
    assert config["mode"] == "poll"
    assert "nonce" not in config
    assert calls["celery"] == 1
    assert calls["blocking"] == 0


def test_each_browser_config_gets_a_fresh_python_nonce(monkeypatch):
    _patches(monkeypatch, api=_http_api())
    nonces = iter(["a" * 64, "b" * 64])
    monkeypatch.setattr(orchestration, "new_nonce", lambda: next(nonces))

    first = _config(orchestration.prepare_html(_request(), _html(), fragment=False))
    second = _config(orchestration.prepare_html(_request(), _html(), fragment=False))
    assert first["api"]["url"].endswith(f"nonce={'a' * 64}")
    assert second["api"]["url"].endswith(f"nonce={'b' * 64}")


def test_existing_api_query_is_preserved(monkeypatch):
    api = TailwindAPI(
        url="https://example.com/compile?foo=bar&nonce=old",
        transport="http",
        token="",
        timeout=30,
    )
    _patches(monkeypatch, api=api)
    config = _config(orchestration.prepare_html(_request(), _html(), fragment=False))
    url = config["api"]["url"]
    assert "foo=bar" in url
    assert url.count("nonce=") == 1
    assert "nonce=old" not in url


def test_wsgi_celery_http_api_uses_js(monkeypatch):
    calls = _patches(monkeypatch, celery=True, api=_http_api())
    config = _config(orchestration.prepare_html(_request(), _html(), fragment=False))
    assert config["mode"] == "http"
    assert calls["celery"] == 0


def test_asgi_no_api_no_celery_submits(monkeypatch):
    calls = _patches(monkeypatch)
    config = _config(
        orchestration.prepare_html(_request(asgi=True), _html(), fragment=False)
    )
    assert config["mode"] == "poll"
    assert calls["submit"] == 1
    assert calls["blocking"] == 0


def test_asgi_http_api_uses_python(monkeypatch):
    calls = _patches(monkeypatch, api=_http_api())
    config = _config(
        orchestration.prepare_html(_request(asgi=True), _html(), fragment=False)
    )
    assert config["mode"] == "poll"
    assert calls["submit"] == 1


def test_asgi_websocket_api_uses_js(monkeypatch):
    calls = _patches(monkeypatch, api=_ws_api())
    config = _config(
        orchestration.prepare_html(_request(asgi=True), _html(), fragment=False)
    )
    assert config["mode"] == "ws"
    assert calls["submit"] == 0


def test_cache_hit_bypasses_everything(monkeypatch):
    calls = _patches(monkeypatch, output=".cached{}", celery=True, api=_http_api())
    config = _config(orchestration.prepare_html(_request(), _html(), fragment=False))
    assert config["mode"] == "fetch"
    assert "nonce" not in config
    assert calls == {"blocking": 0, "http": 0, "celery": 0, "submit": 0}


def test_token_http_api_uses_python_on_wsgi(monkeypatch):
    api = _http_api(token="secret")  # noqa: S106
    calls = _patches(monkeypatch, api=api)
    config = _config(orchestration.prepare_html(_request(), _html(), fragment=False))
    assert config["mode"] == "fetch"
    assert calls["http"] == 1
    assert "secret" not in json.dumps(config)


def test_token_websocket_api_falls_back(monkeypatch):
    api = _ws_api(token="secret")  # noqa: S106
    calls = _patches(monkeypatch, api=api)
    config = _config(orchestration.prepare_html(_request(), _html(), fragment=False))
    assert config["mode"] == "fetch"
    assert calls["blocking"] == 1


def test_celery_dispatch_failure_falls_back(monkeypatch):
    calls = _patches(monkeypatch, celery=False)
    config = _config(orchestration.prepare_html(_request(), _html(), fragment=False))
    assert config["mode"] == "fetch"
    assert calls["blocking"] == 1


def test_fragment_config_is_injected(monkeypatch):
    _patches(monkeypatch)
    updated = orchestration.prepare_html(
        _request(),
        _html(fragment=True),
        fragment=True,
    )
    assert updated is not None
    assert updated.startswith('<script id="daisyui-jit-config-')
    assert _config(updated)["mode"] == "fetch"


@override_settings(WAGTAIL_DAISIE_TAILWIND_POLL_INTERVAL=10)
def test_poll_settings_are_rendered(monkeypatch):
    _patches(monkeypatch, celery=True)
    config = _config(orchestration.prepare_html(_request(), _html(), fragment=False))
    assert config["poll"]["initial"] == 10
