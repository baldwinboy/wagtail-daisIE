from unittest.mock import Mock, patch

import pytest

from django.test import override_settings

from wagtail_daisIE.tailwindcss import api


@override_settings(TAILWIND_CSS_API="https://example.com/compile")
def test_legacy_string_api_is_supported():
    parsed = api.get_tailwind_api()
    assert parsed is not None
    assert parsed.transport == "http"
    assert parsed.url == "https://example.com/compile"


@override_settings(
    TAILWIND_CSS_API={
        "url": "wss://example.com/compile",
        "transport": "websocket",
    }
)
def test_websocket_api_dict():
    parsed = api.get_tailwind_api()
    assert parsed is not None
    assert parsed.transport == "websocket"


@override_settings(
    TAILWIND_CSS_API={
        "url": "https://example.com/compile",
        "transport": "websocket",
    }
)
def test_transport_and_scheme_must_match():
    assert api.get_tailwind_api() is None
    assert api.tailwind_api_error() == (
        "TAILWIND_CSS_API URL scheme does not match its transport."
    )


@override_settings(
    TAILWIND_CSS_API={
        "url": "https://example.com/compile",
        "token": "secret",
    }
)
def test_token_is_not_exposed_to_js():
    parsed = api.get_tailwind_api()
    assert parsed is not None
    assert api.js_api_config(parsed, nonce="a" * 64) is None


@override_settings(TAILWIND_CSS_API={"url": "https://example.com/compile"})
def test_js_config_contains_server_built_nonce_url():
    parsed = api.get_tailwind_api()
    assert parsed is not None
    assert api.js_api_config(parsed, nonce="a" * 64) == {
        "url": f"https://example.com/compile?nonce={'a' * 64}",
        "transport": "http",
    }


def test_append_nonce_preserves_existing_query():
    assert api.append_nonce("https://example.com/compile?foo=bar", "abc") == (
        "https://example.com/compile?foo=bar&nonce=abc"
    )


def test_append_nonce_replaces_existing_nonce():
    assert (
        api.append_nonce("https://example.com/compile?nonce=old&foo=bar", "new")
        == "https://example.com/compile?foo=bar&nonce=new"
    )


def test_append_nonce_preserves_fragment():
    assert api.append_nonce("https://example.com/compile#frag", "abc") == (
        "https://example.com/compile?nonce=abc#frag"
    )


def test_append_nonce_does_not_touch_similar_keys():
    assert api.append_nonce("https://example.com/compile?xnonce=old", "abc") == (
        "https://example.com/compile?xnonce=old&nonce=abc"
    )


def test_new_nonce_is_hex_and_unique():
    first = api.new_nonce()
    second = api.new_nonce()
    assert len(first) == 64
    assert first != second
    int(first, 16)


def test_compile_via_http_posts_and_validates():
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"stylesheet": ".a { color: red; }"}
    parsed = api.TailwindAPI(
        url="https://example.com/compile",
        transport="http",
        token="secret",  # noqa: S106
        timeout=5,
    )

    with patch(
        "wagtail_daisIE.tailwindcss.api.requests.post", return_value=response
    ) as post:
        result = api.compile_via_http(".input { color: red; }", parsed)

    assert result == ".a { color: red; }"
    headers = post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer secret"
    assert "X-Tailwind-Nonce" not in headers
    url = post.call_args.args[0]
    assert url.startswith("https://example.com/compile?nonce=")
    assert len(url.rsplit("nonce=", 1)[1]) == 64
    assert post.call_args.kwargs["json"] == {"stylesheet": ".input { color: red; }"}


def test_compile_via_http_accepts_explicit_nonce():
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"stylesheet": ".a { color: red; }"}
    parsed = api.TailwindAPI(
        url="https://example.com/compile",
        transport="http",
        token="",
        timeout=5,
    )

    with patch(
        "wagtail_daisIE.tailwindcss.api.requests.post", return_value=response
    ) as post:
        api.compile_via_http(".input { color: red; }", parsed, nonce="fixed")

    assert post.call_args.args[0].endswith("?nonce=fixed")
    assert "X-Tailwind-Nonce" not in post.call_args.kwargs["headers"]


def test_compile_via_http_uses_a_fresh_nonce_per_call():
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"stylesheet": ".a { color: red; }"}
    parsed = api.TailwindAPI(
        url="https://example.com/compile",
        transport="http",
        token="",
        timeout=5,
    )

    with patch(
        "wagtail_daisIE.tailwindcss.api.requests.post", return_value=response
    ) as post:
        api.compile_via_http(".input { color: red; }", parsed)
        api.compile_via_http(".input { color: red; }", parsed)

    first = post.call_args_list[0].args[0]
    second = post.call_args_list[1].args[0]
    assert first != second
    assert first.startswith("https://example.com/compile?nonce=")
    assert second.startswith("https://example.com/compile?nonce=")


def test_compile_via_http_rejects_invalid_response():
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"stylesheet": "<script>alert(1)</script>"}
    parsed = api.TailwindAPI(
        url="https://example.com/compile",
        transport="http",
        token="",
        timeout=5,
    )

    with patch("wagtail_daisIE.tailwindcss.api.requests.post", return_value=response):
        with pytest.raises(api.TailwindAPIError):
            api.compile_via_http(".input { color: red; }", parsed)
