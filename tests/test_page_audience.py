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


def _page(keys, *, denied="403", redirect_page=None):
    class Page(PageAudienceMixin, _Base):
        audience = [_Block({"audience": keys})]
        audience_denied = denied
        audience_denied_page_id = 1 if redirect_page is not None else None
        audience_denied_page = redirect_page

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
    def test_no_audience_is_allowed(self, rules):
        page = _page([])
        assert page.page_audience_allowed(_Request()) is True
        assert page.serve(_Request()) == "served"

    def test_allowed_when_rule_passes(self, rules):
        page = _page(["adults"])
        assert page.page_audience_allowed(_Request(is_adult=True)) is True
        assert page.serve(_Request(is_adult=True)) == "served"

    def test_denied_raises_404(self, rules):
        page = _page(["adults"], denied="404")
        assert page.page_audience_allowed(_Request()) is False
        with pytest.raises(Http404):
            page.serve(_Request())

    def test_denied_renders_403(self, rules):
        page = _page(["adults"], denied="403")
        response = page.serve(_Request())
        assert response.status_code == 403

    def test_denied_redirects(self, rules):
        class Target:
            url = "/no-access/"

        page = _page(["adults"], denied="redirect", redirect_page=Target())
        response = page.serve(_Request())
        assert response.status_code == 302
        assert response["Location"] == "/no-access/"
