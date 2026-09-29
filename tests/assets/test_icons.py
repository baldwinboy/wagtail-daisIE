from types import SimpleNamespace
from unittest.mock import patch

import pytest

from django.core.cache import cache
from django.template import Context, Template
from django.urls import reverse

from wagtail_daisIE.icons import render_icon, split_icon, validate_icon
from wagtail_daisIE.icons.providers.iconify import ICONIFY_ICON_SCRIPT, IconifyProvider
from wagtail_daisIE.icons.value import IconValueError


class TestIconValue:
    def test_split_legacy_and_malformed(self):
        assert split_icon("mdi:home") == ("mdi", "home")
        assert str(validate_icon("mdi:home")) == "mdi:home"
        # A legacy raw-class value has no prefix and is not a valid icon.
        assert split_icon("fa-solid fa-home") == (None, "fa-solid fa-home")
        with pytest.raises(IconValueError):
            validate_icon("fa-solid fa-home")
        for value in ("bad prefix:home", "mdi", ":home", "mdi:"):
            with pytest.raises(IconValueError):
                validate_icon(value)


class TestWagtailIconRendering:
    def test_svg_legacy_and_template_tag(self):
        html = render_icon("wagtail:home")
        assert "<svg" in html
        assert 'aria-hidden="true"' in html
        # Inline SVG scales with the parent's font-size and colour.
        assert 'width="1em"' in html
        assert 'height="1em"' in html
        assert "currentColor" in html

        assert (
            render_icon("fa-solid fa-home")
            == '<i class="fa-solid fa-home" aria-hidden="true"></i>'
        )

        template = Template(
            '{% load wagtail_daisIE_tags %}{% daisyui_icon "wagtail:home" %}'
        )
        assert "<svg" in template.render(Context({}))


class TestIconifyProvider:
    def test_cached_svg_sanitises_and_escapes(self, settings):
        from wagtail_daisIE.icons.providers.iconify import _sanitize_svg

        settings.WAGTAIL_DAISIE_ICONS = {"iconify": {"mode": "cached-svg"}}
        settings.CACHES = {
            "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
        }
        cache.clear()
        provider = IconifyProvider(
            prefix="mdi", label="MDI", api_base="https://api.example"
        )
        hostile = (
            '<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)">'
            "<script>alert(2)</script>"
            "<path d=\"M0 0\" onclick='alert(3)'/>"
            '<a href="javascript:alert(4)"><rect/></a>'
            '<foreignObject><iframe src="//evil"></iframe></foreignObject>'
            '<use xlink:href="//evil#x"/>'
            "</svg>"
        )
        with patch.object(
            provider,
            "_get",
            return_value=SimpleNamespace(text=hostile, raise_for_status=lambda: None),
        ):
            html = provider.render("home", size="2em")
        assert "<svg" in html and "<path" in html
        for danger in (
            "script",
            "onload",
            "onclick",
            "javascript:",
            "foreignObject",
            "iframe",
            "evil",
            "xlink",
        ):
            assert danger not in html, danger
        assert 'aria-hidden="true"' in html
        assert _sanitize_svg("") == "" and _sanitize_svg("not an svg") == ""

        # ``size``/``color`` land in an attribute, so they cannot break out.
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>'
        with patch.object(provider, "_get_svg", return_value=svg):
            escaped = provider.render("home", size='1em" onload="alert(1)')
        assert 'onload="alert(1)' not in escaped
        assert "&quot;" in escaped

    def test_component_mode_renders_web_component(self, settings):
        settings.WAGTAIL_DAISIE_ICONS = {"iconify": {"mode": "component"}}
        provider = IconifyProvider(prefix="mdi", label="MDI")
        html = provider.render("home")
        assert "<iconify-icon" in html and 'icon="mdi:home"' in html
        assert provider.head_assets() == [
            {"type": "script", "url": ICONIFY_ICON_SCRIPT}
        ]


@pytest.mark.django_db
class TestIconSources:
    def test_icon_search_endpoint_returns_wagtail_icons(self, admin_client):
        response = admin_client.get(
            reverse("wagtail_daisIE:icon_search"),
            {"prefix": "wagtail", "q": "home"},
        )
        assert response.status_code == 200
        values = [icon["value"] for icon in response.json()["icons"]]
        assert "wagtail:home" in values
