import pytest

from django.http import Http404
from django.test import RequestFactory

from wagtail_daisIE.errors.handlers import (
    handler404,
    handler500,
    render_error_page,
)
from wagtail_daisIE.errors.models import ErrorPage


pytestmark = pytest.mark.django_db


class TestRenderErrorPage:
    def test_uses_designed_page(self):
        ErrorPage.objects.create(status_code=404, title="Lost in the bakery", body=[])
        response = render_error_page(RequestFactory().get("/missing"), 404)
        assert response.status_code == 404
        assert b"Lost in the bakery" in response.content

    def test_inactive_page_falls_back(self):
        ErrorPage.objects.create(status_code=404, title="Hidden", is_active=False)
        response = render_error_page(RequestFactory().get("/missing"), 404)
        assert response.status_code == 404
        assert b"Hidden" not in response.content
        assert b"Error 404" in response.content

    def test_status_code_is_used(self):
        ErrorPage.objects.create(status_code=500, title="Boom", body=[])
        response = render_error_page(RequestFactory().get("/"), 500)
        assert response.status_code == 500
        assert b"Boom" in response.content


class TestHandlers:
    def test_handler404(self):
        response = handler404(RequestFactory().get("/missing"), Http404())
        assert response.status_code == 404

    def test_handler500(self):
        response = handler500(RequestFactory().get("/"))
        assert response.status_code == 500


class TestErrorPageModel:
    def test_str(self):
        page = ErrorPage.objects.create(status_code=403, title="Nope", body=[])
        assert str(page) == "403 — Nope"
