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
    def test_uses_designed_page_and_inactive_falls_back(self):
        for status_code, title in [(404, "Lost in the bakery"), (500, "Boom")]:
            ErrorPage.objects.create(status_code=status_code, title=title, body=[])
            response = render_error_page(RequestFactory().get("/missing"), status_code)
            assert response.status_code == status_code
            assert title.encode() in response.content

        ErrorPage.objects.create(status_code=403, title="Hidden", is_active=False)
        response = render_error_page(RequestFactory().get("/missing"), 403)
        assert response.status_code == 403
        assert b"Hidden" not in response.content
        assert b"Error 403" in response.content


class TestHandlers:
    def test_handlers(self):
        """The opt-in contract: a project exposes these in its URLconf."""
        ErrorPage.objects.create(status_code=404, title="Designed 404", body=[])
        response = handler404(RequestFactory().get("/missing"), Http404())
        assert response.status_code == 404
        assert b"Designed 404" in response.content
        assert handler500(RequestFactory().get("/")).status_code == 500
