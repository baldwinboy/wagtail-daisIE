import gzip

import pytest

from django.core.cache import cache
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.test import RequestFactory

from wagtail_daisIE.middleware import TailwindCSSMiddleware
from wagtail_daisIE.tailwindcss import compiler


pytestmark = pytest.mark.django_db


def _middleware(response, request=None):
    request = request or RequestFactory().get("/")
    return TailwindCSSMiddleware(lambda _request: response), request


def _page(body='<div class="flex"></div>', placeholder=True, status=200):
    style = '<style id="daisyui-jit-styles"></style>' if placeholder else ""
    return HttpResponse(
        f"<html><head>{style}</head><body>{body}</body></html>",
        status=status,
    )


def test_injects_into_full_page(monkeypatch):
    cache.clear()
    monkeypatch.setattr(compiler, "_compile_stylesheet", lambda *_: "/* css */")
    middleware, request = _middleware(_page())
    response = middleware(request)
    assert b"/* css */" in response.content
    cache.clear()


def test_injects_into_non_200_page(monkeypatch):
    cache.clear()
    monkeypatch.setattr(compiler, "_compile_stylesheet", lambda *_: "/* css */")
    middleware, request = _middleware(_page(status=404))
    response = middleware(request)
    assert b"/* css */" in response.content
    cache.clear()


def test_extracts_body_and_data_attribute_classes(monkeypatch):
    cache.clear()
    seen = {}

    def fake_compile(stylesheet, session):
        seen["stylesheet"] = stylesheet
        return "/* css */"

    monkeypatch.setattr(compiler, "_compile_stylesheet", fake_compile)
    body = (
        '<div data-daisie-selected-class="btn-primary btn-active">'
        '<span class="grid"></span></div>'
    )
    response = _page(body=body)
    response.content = response.content.replace(b"<body>", b'<body class="flex">')
    middleware, request = _middleware(response)
    middleware(request)

    stylesheet = seen["stylesheet"]
    assert '@source inline("flex");' in stylesheet
    assert '@source inline("grid");' in stylesheet
    assert '@source inline("btn-{active,primary}");' in stylesheet
    cache.clear()


def test_fills_multiple_placeholders(monkeypatch):
    cache.clear()
    monkeypatch.setattr(compiler, "_compile_stylesheet", lambda *_: "/* css */")
    html = (
        "<html><head>"
        '<style id="daisyui-jit-styles"></style>'
        '<style id="daisyui-jit-styles" nonce="n"></style>'
        '</head><body><div class="flex"></div></body></html>'
    )
    middleware, request = _middleware(HttpResponse(html))
    response = middleware(request)
    assert response.content.count(b"/* css */") == 2
    cache.clear()


def test_htmx_fragment_gets_prepended_style(monkeypatch):
    cache.clear()
    monkeypatch.setattr(compiler, "_compile_stylesheet", lambda *_: "/* css */")
    request = RequestFactory().get("/feed/")
    request.htmx = True
    middleware, request = _middleware(
        HttpResponse('<div class="grid gap-4"></div>'), request
    )
    response = middleware(request)
    assert response.content.startswith(b"<style data-daisie-jit>/* css */</style>")
    cache.clear()


def test_full_page_without_placeholder_is_untouched(monkeypatch):
    cache.clear()
    called = []

    def fake_compile(*_):
        called.append(True)
        return "/* css */"

    monkeypatch.setattr(compiler, "_compile_stylesheet", fake_compile)
    response = _page(placeholder=False)
    original = response.content
    middleware, request = _middleware(response)
    middleware(request)
    assert response.content == original
    assert called == []
    cache.clear()


def test_htmx_fragment_without_classes_is_untouched(monkeypatch):
    cache.clear()
    monkeypatch.setattr(compiler, "_compile_stylesheet", lambda *_: "/* css */")
    request = RequestFactory().get("/feed/")
    request.htmx = True
    response = HttpResponse("<p>No classes here</p>")
    original = response.content
    middleware, request = _middleware(response, request)
    middleware(request)
    assert response.content == original
    cache.clear()


def test_json_and_streaming_responses_are_skipped(monkeypatch):
    cache.clear()
    monkeypatch.setattr(compiler, "_compile_stylesheet", lambda *_: "/* css */")
    middleware, request = _middleware(JsonResponse({"ok": True}))
    assert middleware(request).content == b'{"ok": true}'

    streaming = StreamingHttpResponse(iter([b"<html></html>"]))
    middleware, request = _middleware(streaming)
    assert middleware(request) is streaming
    cache.clear()


def test_compilation_failure_leaves_response_untouched(monkeypatch):
    cache.clear()

    def fail(*_):
        raise compiler.TailwindCompilationError("no compiler")

    monkeypatch.setattr(compiler, "_compile_stylesheet", fail)
    response = _page()
    original = response.content
    middleware, request = _middleware(response)
    middleware(request)
    assert response.content == original
    cache.clear()


def test_gzip_round_trip(monkeypatch):
    cache.clear()
    monkeypatch.setattr(compiler, "_compile_stylesheet", lambda *_: "/* css */")
    html = b'<html><head><style id="daisyui-jit-styles"></style></head><body class="flex"></body></html>'
    response = HttpResponse(gzip.compress(html))
    response["Content-Encoding"] = "gzip"
    middleware, request = _middleware(response)
    response = middleware(request)
    decoded = gzip.decompress(response.content)
    assert b"/* css */" in decoded
    cache.clear()
