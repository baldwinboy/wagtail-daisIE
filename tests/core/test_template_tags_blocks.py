import pytest

from django.template import Context, Template

from wagtail_daisIE.menus.models import DaisyUIMenu
from wagtail_daisIE.models import (
    BackgroundLayer,
    DaisyUITheme,
    DaisyUIThemeBackground,
    DaisyUIThemeColors,
    DaisyUIThemeFontCDN,
    DaisyUIThemeFontFamily,
    DaisyUIThemeFonts,
)


pytestmark = pytest.mark.django_db


def _make_theme(name, *, default=False):
    theme = DaisyUITheme.objects.create(name=name, default=default)
    DaisyUIThemeColors.objects.create(theme=theme)
    return theme


@pytest.fixture
def theme():
    return _make_theme("test-theme", default=True)


@pytest.fixture
def theme_with_background():
    theme = _make_theme("background-theme")
    bg = DaisyUIThemeBackground.objects.create(theme=theme)
    BackgroundLayer.objects.create(background=bg, layer_type="solid", color="#ff0000ff")
    return theme


@pytest.fixture
def theme_with_fonts():
    theme = _make_theme("fonts-theme")
    fonts = DaisyUIThemeFonts.objects.create(theme=theme)
    DaisyUIThemeFontFamily.objects.create(
        fonts=fonts, role="heading", font_family="Roboto"
    )
    DaisyUIThemeFontCDN.objects.create(
        theme=theme,
        url="https://fonts.googleapis.com/css2?family=Roboto",
        label="Google Fonts",
    )
    return theme


def _render(source, context):
    return Template("{% load wagtail_daisIE_tags %}" + source).render(Context(context))


class TestThemeCss:
    def test_renders_and_inlines_css(self, theme):
        html = _render("{% daisyui_theme_css theme %}", {"theme": theme})
        assert '[data-theme="test-theme"]' in html
        assert "--color-primary:" in html

        inlined = _render(
            "{% daisyui_theme_inline_css theme as css %}{{ css }}", {"theme": theme}
        )
        assert "--color-primary:" in inlined
        assert "<style" not in inlined

    def test_background_css_with_and_without(self, theme, theme_with_background):
        with_bg = _render(
            "{% daisyui_theme_background_css theme %}", {"theme": theme_with_background}
        )
        assert "background:" in with_bg and "#ff0000ff" in with_bg
        without = _render("{% daisyui_theme_background_css theme %}", {"theme": theme})
        assert "background:" not in without

    def test_font_css_and_cdn(self, theme, theme_with_fonts):
        fonts = _render(
            "{% daisyui_theme_font_css theme %}", {"theme": theme_with_fonts}
        )
        assert "--font-heading:" in fonts and "Roboto" in fonts
        assert "--font-heading" not in _render(
            "{% daisyui_theme_font_css theme %}", {"theme": theme}
        )
        cdn = _render(
            "{% daisyui_theme_font_cdns theme %}", {"theme": theme_with_fonts}
        )
        assert "fonts.googleapis.com" in cdn

    def test_full_css_combines_colors_and_fonts(self, theme_with_fonts):
        html = _render(
            "{% daisyui_theme_full_css theme %}", {"theme": theme_with_fonts}
        )
        assert "--color-primary:" in html
        assert "--font-heading:" in html


class TestMenuTag:
    def test_layouts_and_css_class(self):
        for layout, url, label, expected in [
            ("navbar", "https://example.com", "Home", "navbar"),
            ("footer", "https://example.com/privacy", "Privacy", "footer"),
            ("sidebar", "/dashboard", "Dashboard", "drawer"),
        ]:
            menu = DaisyUIMenu.objects.create(name=f"{layout} nav", layout=layout)
            menu.body = [
                {
                    "type": "link",
                    "value": {
                        "text": label,
                        "destination": [{"type": "link_url", "value": url}],
                        "open_in_new_tab": False,
                    },
                }
            ]
            menu.save()
            html = _render('{% daisyui_menu "' + layout + ' nav" %}', {})
            assert f'href="{url}"' in html
            assert label in html and expected in html

        styled = DaisyUIMenu.objects.create(name="Styled Nav", layout="navbar")
        styled.body = [
            {
                "type": "link",
                "value": {
                    "text": "Home",
                    "destination": [{"type": "link_url", "value": "/home"}],
                    "open_in_new_tab": False,
                },
            }
        ]
        styled.save()
        html = _render('{% daisyui_menu "Styled Nav" css_class="bg-base-200" %}', {})
        assert "bg-base-200" in html and "Home" in html

    def test_nonexistent_menu_renders_nothing(self):
        DaisyUIMenu.objects.create(name="Known", layout="navbar")
        template = Template(
            "{% load wagtail_daisIE_tags %}{% daisyui_menu name css_class=extra %}"
        )
        assert (
            template.render(Context({"name": "Nonexistent", "extra": ""})).strip() == ""
        )
        assert template.render(Context({"name": "Known", "extra": ""})).strip() != ""
