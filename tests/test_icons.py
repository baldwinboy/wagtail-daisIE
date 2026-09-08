from unittest.mock import patch

import pytest

from django.template import Context, Template
from django.urls import reverse

from wagtail_daisIE.icons import render_icon, split_icon, validate_icon
from wagtail_daisIE.icons.providers.iconify import IconifyProvider
from wagtail_daisIE.icons.value import IconValueError
from wagtail_daisIE.models import DaisyUIIconSource


class TestIconValue:
    def test_split_universal(self):
        assert split_icon("mdi:home") == ("mdi", "home")

    def test_split_legacy(self):
        assert split_icon("fa-solid fa-home") == (None, "fa-solid fa-home")

    def test_split_empty(self):
        assert split_icon("") == (None, None)

    def test_validate(self):
        assert str(validate_icon("mdi:home")) == "mdi:home"

    def test_validate_rejects_malformed(self):
        for value in ("bad prefix:home", "mdi", ":home", "mdi:"):
            with pytest.raises(IconValueError):
                validate_icon(value)


class TestWagtailIconRendering:
    def test_renders_inline_svg(self):
        html = render_icon("wagtail:home")
        assert "<svg" in html
        assert 'aria-hidden="true"' in html

    def test_unknown_icon_is_empty(self):
        assert render_icon("wagtail:does-not-exist") == ""

    def test_legacy_class_value(self):
        assert (
            render_icon("fa-solid fa-home")
            == '<i class="fa-solid fa-home" aria-hidden="true"></i>'
        )

    def test_template_tag(self):
        template = Template(
            '{% load wagtail_daisIE_tags %}{% daisyui_icon "wagtail:home" %}'
        )
        assert "<svg" in template.render(Context({}))


class TestIconifyProvider:
    def test_cached_svg_mode_renders_inline_svg(self, settings):
        settings.WAGTAIL_DAISIE_ICONS = {"iconify": {"mode": "cached-svg"}}
        provider = IconifyProvider(
            prefix="mdi", label="MDI", api_base="https://api.example"
        )
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M0 0"/></svg>'
        with patch.object(provider, "_get_svg", return_value=svg):
            html = provider.render("home", size="2em")
        assert "<svg" in html
        assert 'aria-hidden="true"' in html

    def test_component_mode_renders_web_component(self, settings):
        settings.WAGTAIL_DAISIE_ICONS = {"iconify": {"mode": "component"}}
        provider = IconifyProvider(prefix="mdi", label="MDI")
        html = provider.render("home")
        assert "<iconify-icon" in html
        assert 'icon="mdi:home"' in html

    def test_component_mode_declares_script_asset(self, settings):
        settings.WAGTAIL_DAISIE_ICONS = {"iconify": {"mode": "component"}}
        provider = IconifyProvider(prefix="mdi", label="MDI")
        assets = provider.head_assets()
        assert assets and assets[0]["type"] == "script"


@pytest.mark.django_db
class TestIconSources:
    def test_default_sources_are_seeded(self):
        assert DaisyUIIconSource.objects.filter(prefix="mdi").exists()

    def test_icon_search_endpoint_returns_wagtail_icons(self, admin_client):
        response = admin_client.get(
            reverse("wagtail_daisIE:icon_search"),
            {"prefix": "wagtail", "q": "home"},
        )
        assert response.status_code == 200
        values = [icon["value"] for icon in response.json()["icons"]]
        assert "wagtail:home" in values
