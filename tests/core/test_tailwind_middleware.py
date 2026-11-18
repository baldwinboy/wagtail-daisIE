import gzip

import pytest

from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.test import RequestFactory

from wagtail_daisIE.middleware import TailwindCSSMiddleware
from wagtail_daisIE.tailwindcss import compiler, orchestration


pytestmark = pytest.mark.django_db


def _middleware(response, request=None):
    request = request or RequestFactory().get("/")
    return TailwindCSSMiddleware(lambda _request: response), request


def _page(body='<div class="flex"></div>', status=200):
    return HttpResponse(
        "<html><head>"
        '<script id="daisyui-jit-config" type="application/json">{}</script>'
        f"</head><body>{body}</body></html>",
        status=status,
    )


def test_prepare_html_is_called_for_full_page(monkeypatch):
    seen = {}

    def fake_prepare(request, html_text, *, fragment):
        seen["fragment"] = fragment
        return html_text.replace("{}", '{"mode": "fetch"}')

    monkeypatch.setattr(orchestration, "prepare_html", fake_prepare)
    middleware, request = _middleware(_page())
    response = middleware(request)
    assert b'"mode": "fetch"' in response.content
    assert seen["fragment"] is False


def test_prepare_html_is_called_for_non_200(monkeypatch):
    seen = []
    monkeypatch.setattr(
        orchestration,
        "prepare_html",
        lambda request, html, *, fragment: seen.append(True) or html,
    )
    middleware, request = _middleware(_page(status=404))
    middleware(request)
    assert seen == [True]


def test_htmx_fragment_flag(monkeypatch):
    seen = {}
    request = RequestFactory().get("/feed/")
    request.htmx = True

    def fake_prepare(request, html, *, fragment):
        seen["fragment"] = fragment
        return html

    monkeypatch.setattr(orchestration, "prepare_html", fake_prepare)
    middleware, request = _middleware(HttpResponse('<div class="grid"></div>'), request)
    middleware(request)
    assert seen["fragment"] is True


def test_no_changes_when_prepare_returns_none(monkeypatch):
    monkeypatch.setattr(orchestration, "prepare_html", lambda *args, **kwargs: None)
    response = _page()
    original = response.content
    middleware, request = _middleware(response)
    middleware(request)
    assert response.content == original


def test_compilation_error_leaves_response_untouched(monkeypatch):
    def fail(*args, **kwargs):
        raise compiler.TailwindCompilationError("no compiler")

    monkeypatch.setattr(orchestration, "prepare_html", fail)
    response = _page()
    original = response.content
    middleware, request = _middleware(response)
    middleware(request)
    assert response.content == original


def test_json_and_streaming_responses_are_skipped(monkeypatch):
    monkeypatch.setattr(
        orchestration,
        "prepare_html",
        lambda request, html, *, fragment: html,
    )
    middleware, request = _middleware(JsonResponse({"ok": True}))
    assert middleware(request).content == b'{"ok": true}'

    streaming = StreamingHttpResponse(iter([b"<html></html>"]))
    middleware, request = _middleware(streaming)
    assert middleware(request) is streaming


def test_gzip_round_trip(monkeypatch):
    monkeypatch.setattr(
        orchestration,
        "prepare_html",
        lambda request, html, *, fragment: html.replace("{}", '{"mode": "fetch"}'),
    )
    html = (
        b'<html><head><script id="daisyui-jit-config" '
        b'type="application/json">{}</script></head>'
        b'<body class="flex"></body></html>'
    )
    response = HttpResponse(gzip.compress(html))
    response["Content-Encoding"] = "gzip"
    middleware, request = _middleware(response)
    response = middleware(request)
    decoded = gzip.decompress(response.content)
    assert b'"mode": "fetch"' in decoded
