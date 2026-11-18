import pytest

from django.core.cache import cache
from django.test import RequestFactory

from wagtail_daisIE.tailwindcss import artifacts, views


pytestmark = pytest.mark.django_db


def test_token_is_content_addressed():
    first = artifacts.token_for("a")
    second = artifacts.token_for("a")
    assert first == second
    assert len(first) == 64
    assert artifacts.token_for("b") != first


def test_input_output_and_error_round_trip():
    cache.clear()
    token = artifacts.store_input("input")
    assert artifacts.get_input(token) == "input"

    artifacts.store_output(token, "output")
    assert artifacts.get_output(token) == "output"

    artifacts.store_error(token, "boom")
    assert artifacts.get_error(token) == "boom"
    artifacts.store_output(token, "output-2")
    assert artifacts.get_error(token) is None
    cache.clear()


def test_artifact_view_serves_css():
    cache.clear()
    token = artifacts.store_input("input")
    artifacts.store_output(token, "output")
    response = views.artifact(RequestFactory().get("/"), token)
    assert response.status_code == 200
    assert response.content == b"output"
    assert response["Content-Type"].startswith("text/css")
    assert response["Cache-Control"] == "public, max-age=31536000, immutable"
    assert response["X-Content-Type-Options"] == "nosniff"
    cache.clear()


def test_artifact_view_pending_and_error():
    cache.clear()
    token = artifacts.store_input("input")
    pending = views.artifact(RequestFactory().get("/"), token)
    assert pending.status_code == 404

    artifacts.store_error(token, "details should not leak")
    error = views.artifact(RequestFactory().get("/"), token)
    assert error.status_code == 500
    assert b"details should not leak" not in error.content
    cache.clear()


def test_input_view():
    cache.clear()
    token = artifacts.store_input("input")
    response = views.input(RequestFactory().get("/"), token)
    assert response.status_code == 200
    assert response.content == b"input"
    cache.clear()


def test_views_reject_invalid_tokens():
    assert views.artifact(RequestFactory().get("/"), "not-a-token").status_code == 404
    assert views.input(RequestFactory().get("/"), "not-a-token").status_code == 404


def test_artifact_urls_reverse():
    token = "0" * 64
    assert artifacts.output_url(token).endswith(f"/artifact/{token}.css")
    assert artifacts.input_url(token).endswith(f"/input/{token}.css")
