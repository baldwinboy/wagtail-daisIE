import pytest

from django.core.exceptions import ValidationError

from wagtail_daisIE.menus.models import DaisyUIMenu
from wagtail_daisIE.models import (
    BackgroundLayer,
    DaisyUITheme,
    DaisyUIThemeBackground,
    DaisyUIThemeFontFallback,
    DaisyUIThemeFontFamily,
    DaisyUIThemeFonts,
    GradientStop,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def theme():
    return DaisyUITheme.objects.create(name="test-theme", default=True)


class TestDaisyUIThemeBackground:
    def test_solid_gradient_and_multi_layer(self, theme):
        solid = DaisyUIThemeBackground.objects.create(theme=theme)
        BackgroundLayer.objects.create(
            background=solid, layer_type="solid", color="#ff0000ff"
        )
        assert solid.get_effective_background() == "#ff0000ff"

        gradient = DaisyUIThemeBackground.objects.create(theme=theme)
        layer = BackgroundLayer.objects.create(
            background=gradient,
            layer_type="gradient",
            gradient_shape="linear-gradient",
            gradient_angle=90,
        )
        GradientStop.objects.create(layer=layer, color="#ff0000ff", position=0)
        GradientStop.objects.create(layer=layer, color="#0000ffff", position=100)
        css = gradient.get_effective_background()
        assert "linear-gradient" in css and "90deg" in css
        assert "#ff0000ff" in css and "#0000ffff" in css

        multi = DaisyUIThemeBackground.objects.create(theme=theme)
        BackgroundLayer.objects.create(
            background=multi, layer_type="solid", color="#ff0000ff", sort_order=0
        )
        BackgroundLayer.objects.create(
            background=multi, layer_type="solid", color="#0000ffff", sort_order=1
        )
        css = multi.get_effective_background()
        assert "#ff0000ff" in css and "#0000ffff" in css


class TestDaisyUIThemeFonts:
    def test_css_values_and_fallbacks(self, theme):
        fonts = DaisyUIThemeFonts.objects.create(theme=theme)
        heading = DaisyUIThemeFontFamily.objects.create(
            fonts=fonts, role="heading", font_family="Roboto"
        )
        assert heading.css_value == "'Roboto', sans-serif"

        body = DaisyUIThemeFontFamily.objects.create(
            fonts=fonts, role="body", font_family="Inter"
        )
        fallback = DaisyUIThemeFontFallback.objects.create(
            font_family=body, name="Roboto"
        )
        assert fallback.css_value == "'Roboto'"
        assert body.css_value == "'Inter', 'Roboto', sans-serif"

    def test_clean_constraints(self, theme):
        fonts = DaisyUIThemeFonts.objects.create(theme=theme)
        DaisyUIThemeFontFamily.objects.create(fonts=fonts, role="body")
        with pytest.raises(ValidationError):
            DaisyUIThemeFontFamily(fonts=fonts, role="body").clean()
        with pytest.raises(ValidationError):
            DaisyUIThemeFontFamily(fonts=fonts, role="custom", name="").clean()


class TestDaisyUIMenu:
    def test_get_theme_falls_back_to_default(self, theme):
        menu = DaisyUIMenu.objects.create(name="Default theme")
        assert menu.get_theme() == theme
