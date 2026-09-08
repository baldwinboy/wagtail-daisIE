import pytest

from django.template import Context, Template

from wagtail_daisIE.models import (
    BackgroundLayer,
    DaisyUIMenu,
    DaisyUITheme,
    DaisyUIThemeBackground,
    DaisyUIThemeColors,
    DaisyUIThemeFontCDN,
    DaisyUIThemeFontFamily,
    DaisyUIThemeFonts,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def theme():
    t = DaisyUITheme.objects.create(name="test-theme", default=True)
    DaisyUIThemeColors.objects.create(theme=t)
    return t


@pytest.fixture
def theme_with_background(theme):
    bg = DaisyUIThemeBackground.objects.create(theme=theme)
    BackgroundLayer.objects.create(
        background=bg,
        layer_type="solid",
        color="#ff0000ff",
    )
    return theme


@pytest.fixture
def theme_with_fonts(theme):
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


class TestDaisyuiThemeCssTag:
    def test_renders_css(self, theme):
        template = Template(
            "{% load wagtail_daisIE_tags %}{% daisyui_theme_css theme %}"
        )
        html = template.render(Context({"theme": theme}))
        assert '[data-theme="test-theme"]' in html
        assert "color-scheme:" in html
        assert "--color-primary:" in html


class TestDaisyuiThemeInlineCssTag:
    def test_returns_css_string(self, theme):
        template = Template(
            "{% load wagtail_daisIE_tags %}"
            "{% daisyui_theme_inline_css theme as css %}"
            "{{ css }}"
        )
        html = template.render(Context({"theme": theme}))
        assert '[data-theme="test-theme"]' in html
        assert "--color-primary:" in html


class TestDaisyuiThemeBackgroundCssTag:
    def test_renders_background_css(self, theme_with_background):
        template = Template(
            "{% load wagtail_daisIE_tags %}{% daisyui_theme_background_css theme %}"
        )
        html = template.render(Context({"theme": theme_with_background}))
        assert "background:" in html
        assert "#ff0000ff" in html

    def test_no_background(self, theme):
        template = Template(
            "{% load wagtail_daisIE_tags %}{% daisyui_theme_background_css theme %}"
        )
        html = template.render(Context({"theme": theme}))
        # Should render empty when no background exists
        assert "background:" not in html


class TestDaisyuiThemeFontCssTag:
    def test_renders_font_css(self, theme_with_fonts):
        template = Template(
            "{% load wagtail_daisIE_tags %}{% daisyui_theme_font_css theme %}"
        )
        html = template.render(Context({"theme": theme_with_fonts}))
        assert "--font-heading:" in html
        assert "Roboto" in html

    def test_no_fonts(self, theme):
        template = Template(
            "{% load wagtail_daisIE_tags %}{% daisyui_theme_font_css theme %}"
        )
        html = template.render(Context({"theme": theme}))
        assert "--font-heading" not in html

    def test_renders_font_cdn(self, theme_with_fonts):
        template = Template(
            "{% load wagtail_daisIE_tags %}{% daisyui_theme_font_cdns theme %}"
        )
        html = template.render(Context({"theme": theme_with_fonts}))
        assert "fonts.googleapis.com" in html


class TestDaisyuiThemeFullCssTag:
    def test_renders_combined_css(self, theme_with_fonts):
        template = Template(
            "{% load wagtail_daisIE_tags %}{% daisyui_theme_full_css theme %}"
        )
        html = template.render(Context({"theme": theme_with_fonts}))
        assert "--color-primary:" in html
        assert "--font-heading:" in html


class TestDaisyuiMenuTag:
    def test_renders_menu(self, theme):
        menu = DaisyUIMenu.objects.create(name="Test Nav", layout="navbar")
        menu.body = [
            {
                "type": "link",
                "value": {
                    "text": "Home",
                    "destination": [
                        {"type": "link_url", "value": "https://example.com"}
                    ],
                    "open_in_new_tab": False,
                },
            }
        ]
        menu.save()
        template = Template(
            '{% load wagtail_daisIE_tags %}{% daisyui_menu "Test Nav" %}'
        )
        html = template.render(Context({}))
        assert "navbar" in html
        assert "Home" in html

    def test_nonexistent_menu(self):
        template = Template(
            '{% load wagtail_daisIE_tags %}{% daisyui_menu "Nonexistent" %}'
        )
        html = template.render(Context({}))
        # Should render nothing for nonexistent menu
        assert html.strip() == ""

    def test_menu_with_css_class(self):
        DaisyUIMenu.objects.create(name="Styled Nav", layout="navbar")
        template = Template(
            "{% load wagtail_daisIE_tags %}"
            '{% daisyui_menu "Styled Nav" css_class="bg-base-200" %}'
        )
        html = template.render(Context({}))
        assert "bg-base-200" in html

    def test_footer_layout(self):
        menu = DaisyUIMenu.objects.create(name="Footer", layout="footer")
        menu.body = [
            {
                "type": "link",
                "value": {
                    "text": "Privacy",
                    "destination": [
                        {"type": "link_url", "value": "https://example.com/privacy"}
                    ],
                    "open_in_new_tab": False,
                },
            }
        ]
        menu.save()
        template = Template('{% load wagtail_daisIE_tags %}{% daisyui_menu "Footer" %}')
        html = template.render(Context({}))
        assert "footer" in html
        assert "Privacy" in html

    def test_sidebar_layout(self):
        menu = DaisyUIMenu.objects.create(name="Sidebar", layout="sidebar")
        menu.body = [
            {
                "type": "link",
                "value": {
                    "text": "Dashboard",
                    "destination": [{"type": "link_url", "value": "/dashboard"}],
                    "open_in_new_tab": False,
                },
            }
        ]
        menu.save()
        template = Template(
            '{% load wagtail_daisIE_tags %}{% daisyui_menu "Sidebar" %}'
        )
        html = template.render(Context({}))
        assert "drawer" in html
        assert "Dashboard" in html
