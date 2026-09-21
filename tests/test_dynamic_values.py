import pytest

from wagtail_daisIE.base_blocks.link import link_url
from wagtail_daisIE.blocks.media import ImageBlock
from wagtail_daisIE.dynamic.resolvers import resolve_dynamic_url


class _Image:
    url = "/media/photo.jpg"
    alt = "A photo"
    title = "Photo"


class _Page:
    def get_absolute_url(self):
        return "/meetings/1/"


class TestDynamicLink:
    def test_dynamic_url_from_attribute(self):
        destination = [{"link_dynamic": "{{ meeting.url }}"}]
        assert link_url(destination, {"meeting": _Image()}) == "/media/photo.jpg"

    def test_dynamic_url_from_get_absolute_url(self):
        destination = [{"link_dynamic": "{{ meeting }}"}]
        assert link_url(destination, {"meeting": _Page()}) == "/meetings/1/"

    def test_dynamic_url_blocks_dangerous_scheme(self):
        assertion = [{"link_dynamic": "{{ bad }}"}]
        assert link_url(assertion, {"bad": "javascript:alert(1)"}) == ""

    def test_static_destination_still_works(self):
        destination = [{"link_url": "https://example.com"}]
        assert link_url(destination, {}) == "https://example.com"

    def test_missing_dynamic_value_is_empty(self):
        assert resolve_dynamic_url("{{ missing.url }}", {}) == ""


class TestDynamicImage:
    def _value(self, expression):
        return {
            "image_source": "dynamic",
            "image_expression": expression,
            "design": {},
            "audience": {},
        }

    def test_resolves_object_url_and_alt(self):
        context = ImageBlock().get_context(self._value("photo"), {"photo": _Image()})
        assert context["resolved_image_url"] == "/media/photo.jpg"
        assert context["resolved_image_alt"] == "A photo"

    def test_resolves_string_url(self):
        context = ImageBlock().get_context(
            self._value("photo_url"), {"photo_url": "/media/x.png"}
        )
        assert context["resolved_image_url"] == "/media/x.png"
        assert context["resolved_image"] is None

    def test_static_source_ignores_expression(self):
        value = {
            "image_source": "static",
            "image_expression": "photo",
            "image": None,
            "design": {},
            "audience": {},
        }
        context = ImageBlock().get_context(value, {"photo": _Image()})
        assert context["resolved_image_url"] == ""
        assert context["resolved_image"] is None

    def test_missing_expression(self):
        context = ImageBlock().get_context(self._value(""), {"photo": _Image()})
        assert context["resolved_image_url"] == ""


class TestSafeScheme:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("https://example.com", "https://example.com"),
            ("/relative/", "/relative/"),
            ("mailto:a@b.com", "mailto:a@b.com"),
            ("tel:123", "tel:123"),
            ("javascript:alert(1)", ""),
            ("data:text/html,<script>", ""),
        ],
    )
    def test_schemes(self, value, expected):
        from wagtail_daisIE.dynamic.resolvers import sanitize_url

        assert sanitize_url(value) == expected
