from types import SimpleNamespace

import pytest

from django.http import Http404

from wagtail_daisIE.base_blocks.audience import PageAudienceMixin


pytestmark = pytest.mark.django_db


class _Block:
    def __init__(self, value):
        self.value = value


class _Base:
    def serve(self, request, *args, **kwargs):
        return "served"


def _page(keys, *, denied="403", destination=None):
    class Page(PageAudienceMixin, _Base):
        audience = [_Block({"audience": keys})]
        audience_denied = denied
        audience_denied_destination = destination or []

    return Page()


class _Request:
    def __init__(self, is_adult=False):
        self.is_adult = is_adult


@pytest.fixture
def rules(settings):
    settings.WAGTAIL_DAISIE_AUDIENCE_RULES = {
        "adults": {
            "label": "Adults",
            "rule": lambda request: getattr(request, "is_adult", False),
        }
    }


class TestPageAudience:
    def test_no_audience_and_allowed(self, rules):
        page = _page([])
        assert page.page_audience_allowed(_Request()) is True
        assert page.serve(_Request()) == "served"

        page = _page(["adults"])
        assert page.page_audience_allowed(_Request(is_adult=True)) is True
        assert page.serve(_Request(is_adult=True)) == "served"

    def test_denied_modes(self, rules):
        assert (
            _page(["adults"], denied="404").page_audience_allowed(_Request()) is False
        )
        with pytest.raises(Http404):
            _page(["adults"], denied="404").serve(_Request())

        assert _page(["adults"], denied="403").serve(_Request()).status_code == 403

    def test_page_destination_redirects(self, rules):
        class Target:
            url = "/no-access/"

        page = _page(
            ["adults"], denied="redirect", destination=[("link_page", Target())]
        )
        response = page.serve(_Request())
        assert response.status_code == 302 and response["Location"] == "/no-access/"

    def test_external_url_and_path_redirect(self, rules):
        page = _page(
            ["adults"],
            denied="redirect",
            destination=[("link_url", "https://example.com/next")],
        )
        response = page.serve(_Request())
        assert (
            response.status_code == 302
            and response["Location"] == "https://example.com/next"
        )

        page = _page(
            ["adults"], denied="redirect", destination=[("link_url", "/local/next")]
        )
        response = page.serve(_Request())
        assert response.status_code == 302 and response["Location"] == "/local/next"

    def test_dynamic_url_resolves_from_context(self, rules):
        class Page(PageAudienceMixin, _Base):
            audience = [_Block({"audience": ["adults"]})]
            audience_denied = "redirect"
            audience_denied_destination = [
                {"type": "link_dynamic", "value": "{{ target.url }}"}
            ]

            def get_daisie_context(self, request):
                return {"target": SimpleNamespace(url="https://example.com/dynamic")}

        page = Page()
        response = page.serve(_Request())
        assert response.status_code == 302
        assert response["Location"] == "https://example.com/dynamic"

    def test_document_email_and_phone_redirect(self, rules):
        class Document:
            url = "/documents/x/"

        page = _page(
            ["adults"], denied="redirect", destination=[("link_document", Document())]
        )
        response = page.serve(_Request())
        assert response.status_code == 302 and response["Location"] == "/documents/x/"

        page = _page(
            ["adults"],
            denied="redirect",
            destination=[("link_email", "member@example.com")],
        )
        response = page.serve(_Request())
        assert (
            response.status_code == 302
            and response["Location"] == "mailto:member@example.com"
        )

        page = _page(
            ["adults"], denied="redirect", destination=[("link_phone", "+123")]
        )
        response = page.serve(_Request())
        assert response.status_code == 302 and response["Location"] == "tel:+123"

    def test_empty_destination_falls_back_to_403(self, rules):
        response = _page(["adults"], denied="redirect", destination=[]).serve(
            _Request()
        )
        assert response.status_code == 403

    def test_unresolvable_destination_falls_back_to_403(self, rules):
        page = _page(
            ["adults"],
            denied="redirect",
            destination=[("link_dynamic", "{{ missing.url }}")],
        )
        response = page.serve(_Request())
        assert response.status_code == 403

    def test_raw_link_page_stream_shape_resolves(self, rules):
        class Target:
            url = "/raw/"

        page = _page(
            ["adults"],
            denied="redirect",
            destination=[{"type": "link_page", "value": Target()}],
        )
        response = page.serve(_Request())
        assert response.status_code == 302 and response["Location"] == "/raw/"

    def test_get_audience_denied_url_directly(self, rules):
        class Target:
            url = "/direct/"

        page = _page(
            ["adults"], denied="redirect", destination=[("link_page", Target())]
        )
        request = _Request()
        assert page.get_audience_denied_url(request) == "/direct/"
        assert (
            _page(
                ["adults"], denied="redirect", destination=[]
            ).get_audience_denied_url(request)
            == ""
        )

    def test_legacy_field_is_removed(self):
        from wagtail_daisIE.pages import StyledPageMixin

        field_names = {field.name for field in StyledPageMixin._meta.get_fields()}
        assert "audience_denied_destination" in field_names
        assert "audience_denied_page" not in field_names

    def test_form_page_serve_uses_audience_denial(self):
        from wagtail_daisIE.forms.models import DaisieFormPage

        page = SimpleNamespace(
            page_audience_allowed=lambda request: False,
            audience_denied_response=lambda request: "denied",
        )
        assert DaisieFormPage.serve(page, _Request()) == "denied"

    def test_detail_page_serve_delegates_to_template(self):
        from wagtail_daisIE.detail_pages.models import ModelDetailPage

        template = SimpleNamespace(
            page_audience_allowed=lambda request: False,
            audience_denied_response=lambda request: "denied",
        )
        page = SimpleNamespace(get_template_page=lambda: template)
        assert ModelDetailPage.serve(page, _Request()) == "denied"
