from wagtail_daisIE.base_blocks.link import link_url
from wagtail_daisIE.blocks.media import ImageBlock


class _Image:
    url = "/media/photo.jpg"
    alt = "A photo"
    title = "Photo"


class _Page:
    def get_absolute_url(self):
        return "/meetings/1/"


class TestDynamicLink:
    def test_dynamic_and_static_destinations(self):
        assert (
            link_url([{"link_dynamic": "{{ meeting.url }}"}], {"meeting": _Image()})
            == "/media/photo.jpg"
        )
        assert (
            link_url([{"link_dynamic": "{{ meeting }}"}], {"meeting": _Page()})
            == "/meetings/1/"
        )
        assert (
            link_url([{"link_dynamic": "{{ bad }}"}], {"bad": "javascript:alert(1)"})
            == ""
        )
        assert (
            link_url([{"link_url": "https://example.com"}], {}) == "https://example.com"
        )


class TestDynamicImage:
    def _value(self, expression, source="dynamic"):
        return {
            "image_source": source,
            "image_expression": expression,
            "image": None,
            "design": {},
            "audience": {},
        }

    def test_resolves_object_string_and_static_source(self):
        context = ImageBlock().get_context(self._value("photo"), {"photo": _Image()})
        assert context["resolved_image_url"] == "/media/photo.jpg"
        assert context["resolved_image_alt"] == "A photo"

        context = ImageBlock().get_context(
            self._value("photo_url"), {"photo_url": "/media/x.png"}
        )
        assert context["resolved_image_url"] == "/media/x.png"
        assert context["resolved_image"] is None

        context = ImageBlock().get_context(
            self._value("photo", source="static"), {"photo": _Image()}
        )
        assert context["resolved_image_url"] == "" and context["resolved_image"] is None


class TestSafeScheme:
    def test_schemes(self):
        from wagtail_daisIE.dynamic.resolvers import sanitize_url

        for value, expected in [
            ("https://example.com", "https://example.com"),
            ("/relative/", "/relative/"),
            ("mailto:a@b.com", "mailto:a@b.com"),
            ("tel:123", "tel:123"),
            ("javascript:alert(1)", ""),
            ("data:text/html,<script>", ""),
        ]:
            assert sanitize_url(value) == expected
