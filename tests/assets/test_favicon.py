import base64

import pytest

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.template import Context, Template
from django.test import RequestFactory
from wagtail.images import get_image_model
from wagtail.models import Page, Site

from wagtail_daisIE.assets.models import MANIFEST_ICONS, DaisyUIFavicon
from wagtail_daisIE.favicon import views as favicon_views


pytestmark = pytest.mark.django_db

#: A 1x1 transparent PNG.
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def _image():
    Image = get_image_model()
    return Image.objects.create(
        title="icon",
        file=SimpleUploadedFile("icon.png", PNG_BYTES, content_type="image/png"),
    )


class TestResolver:
    def test_global_default_and_site_specific(self):
        global_favicon = DaisyUIFavicon.objects.create(app_name="Global")
        request = RequestFactory().get("/")
        assert DaisyUIFavicon.for_request(request) == global_favicon

        root = Page.get_first_root_node()
        site = Site.objects.create(hostname="example.com", port=80, root_page=root)
        specific = DaisyUIFavicon.objects.create(site=site, app_name="Specific")
        request = RequestFactory().get("/", HTTP_HOST="example.com")
        assert DaisyUIFavicon.for_request(request) == specific
        assert DaisyUIFavicon.for_request(request) != global_favicon


class TestManifest:
    def test_manifest_metadata_and_validator(self):
        favicon = DaisyUIFavicon.objects.create(
            image=_image(),
            app_name="Bakery",
            short_name="Bake",
            theme_color="#A1B2C3",
            background_color="#FFFFFF",
        )
        data = favicon.manifest()
        assert data["name"] == "Bakery"
        assert data["theme_color"] == "#A1B2C3"
        assert data["display"] == "standalone"
        assert {icon["sizes"] for icon in data["icons"]} == {
            str(size) for size, _density in MANIFEST_ICONS
        }
        for icon in data["icons"]:
            assert icon["src"] and icon["type"] == "image/png"
            assert set(icon) == {"src", "sizes", "type", "density"}

        blank = DaisyUIFavicon.objects.create(
            image=_image(), theme_color="", background_color=""
        ).manifest()
        assert "name" not in blank and "theme_color" not in blank

        with pytest.raises(ValidationError):
            DaisyUIFavicon(app_name="x", theme_color="not-a-colour").full_clean()


class TestViews:
    def test_browser_config_and_redirect(self):
        favicon = DaisyUIFavicon.objects.create(image=_image(), theme_color="#112233")
        response = favicon_views.browser_config(
            RequestFactory().get("/browser-config.xml")
        )
        response.render()
        assert response["Content-Type"].startswith("application/xml")
        assert b"112233" in response.content

        redirect = favicon_views.favicon(RequestFactory().get("/favicon.ico"))
        assert redirect.status_code == 302
        assert redirect["Location"] == favicon.rendition_url("32x32")

    def test_missing_image_is_404(self):
        DaisyUIFavicon.objects.create(app_name="No image")
        with pytest.raises(Http404):
            favicon_views.manifest(RequestFactory().get("/manifest.json"))


class TestTag:
    def _render(self):
        template = Template("{% load wagtail_daisIE_tags %}{% daisyui_favicon %}")
        request = RequestFactory().get("/")
        return template.render(Context({"request": request}))

    def test_renders_pwa_links_or_nothing(self):
        DaisyUIFavicon.objects.create(image=_image(), theme_color="#445566")
        html = self._render()
        assert 'rel="manifest"' in html
        assert 'rel="apple-touch-icon"' in html
        assert 'name="theme-color"' in html and "#445566" in html

        DaisyUIFavicon.objects.all().delete()
        assert self._render().strip() == ""
