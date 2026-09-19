import pytest

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from wagtail_daisIE.models import (
    BackgroundLayer,
    DaisyUIMenu,
    DaisyUITheme,
    DaisyUIThemeBackground,
    DaisyUIThemeColors,
    DaisyUIThemeFontCDN,
    DaisyUIThemeFontFallback,
    DaisyUIThemeFontFamily,
    DaisyUIThemeFonts,
    GradientStop,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def theme():
    return DaisyUITheme.objects.create(name="test-theme", default=True)


@pytest.fixture
def theme_with_colors(theme):
    DaisyUIThemeColors.objects.create(theme=theme)
    return theme


class TestDaisyUITheme:
    def test_theme_saves_without_draft_state(self):
        from wagtail.models import DraftStateMixin, RevisionMixin

        assert issubclass(DaisyUITheme, RevisionMixin)
        assert not issubclass(DaisyUITheme, DraftStateMixin)

    def test_save_persists_inline_colors(self, theme):
        DaisyUIThemeColors.objects.create(theme=theme, primary="#123456ff")
        assert theme.colors.get().primary == "#123456ff"

    def test_theme_has_help_panel(self):
        from wagtail.admin.panels import HelpPanel

        assert any(isinstance(panel, HelpPanel) for panel in DaisyUITheme.panels)

    def test_inline_panels_limit_to_single_row(self):
        from wagtail.admin.panels import InlinePanel

        inline_panels = {
            panel.relation_name: panel
            for panel in DaisyUITheme.panels
            if isinstance(panel, InlinePanel)
        }
        for relation in ("colors", "radii", "sizes", "effects", "background"):
            assert inline_panels[relation].max_num == 1


class TestBackgroundLayer:
    def test_create_solid(self, theme):
        bg = DaisyUIThemeBackground.objects.create(theme=theme)
        layer = BackgroundLayer.objects.create(
            background=bg,
            layer_type="solid",
            color="#ff0000ff",
        )
        assert layer.layer_type == "solid"
        assert layer.color == "#ff0000ff"

    def test_create_gradient(self, theme):
        bg = DaisyUIThemeBackground.objects.create(theme=theme)
        layer = BackgroundLayer.objects.create(
            background=bg,
            layer_type="gradient",
            gradient_shape="linear-gradient",
            gradient_angle=90,
        )
        stop = GradientStop.objects.create(
            layer=layer,
            color="#ff0000ff",
            position=0,
        )
        assert layer.stops.count() == 1
        assert stop.color == "#ff0000ff"
        assert stop.position == 0

    def test_str(self, theme):
        bg = DaisyUIThemeBackground.objects.create(theme=theme)
        layer = BackgroundLayer.objects.create(background=bg, layer_type="solid")
        assert "Solid" in str(layer)

    def test_gradient_stop_ordering(self, theme):
        bg = DaisyUIThemeBackground.objects.create(theme=theme)
        layer = BackgroundLayer.objects.create(background=bg, layer_type="gradient")
        a = GradientStop.objects.create(
            layer=layer, color="#ff0000ff", position=100, sort_order=1
        )
        b = GradientStop.objects.create(
            layer=layer, color="#0000ffff", position=0, sort_order=0
        )
        assert list(layer.stops.all()) == [b, a]


class TestDaisyUIThemeBackground:
    def test_create(self, theme):
        bg = DaisyUIThemeBackground.objects.create(theme=theme)
        assert bg.theme == theme
        assert bg.layers.count() == 0

    def test_str(self, theme):
        bg = DaisyUIThemeBackground.objects.create(theme=theme)
        assert "background" in str(bg).lower()

    def test_get_effective_background_empty(self, theme_with_colors):
        bg = DaisyUIThemeBackground.objects.create(theme=theme_with_colors)
        css = bg.get_effective_background()
        assert css == "#ffffffff"

    def test_get_effective_background_solid(self, theme):
        bg = DaisyUIThemeBackground.objects.create(theme=theme)
        BackgroundLayer.objects.create(
            background=bg,
            layer_type="solid",
            color="#ff0000ff",
        )
        css = bg.get_effective_background()
        assert css == "#ff0000ff"

    def test_get_effective_background_gradient(self, theme):
        bg = DaisyUIThemeBackground.objects.create(theme=theme)
        layer = BackgroundLayer.objects.create(
            background=bg,
            layer_type="gradient",
            gradient_shape="linear-gradient",
            gradient_angle=90,
        )
        GradientStop.objects.create(layer=layer, color="#ff0000ff", position=0)
        GradientStop.objects.create(layer=layer, color="#0000ffff", position=100)
        css = bg.get_effective_background()
        assert "linear-gradient" in css
        assert "90deg" in css
        assert "#ff0000ff" in css
        assert "#0000ffff" in css

    def test_get_effective_background_multi_layer(self, theme):
        bg = DaisyUIThemeBackground.objects.create(theme=theme)
        BackgroundLayer.objects.create(
            background=bg,
            layer_type="solid",
            color="#ff0000ff",
            sort_order=0,
        )
        BackgroundLayer.objects.create(
            background=bg,
            layer_type="solid",
            color="#0000ffff",
            sort_order=1,
        )
        css = bg.get_effective_background()
        assert "#ff0000ff" in css
        assert "#0000ffff" in css


class TestDaisyUIThemeFonts:
    def test_create_family(self, theme):
        fonts = DaisyUIThemeFonts.objects.create(theme=theme)
        family = DaisyUIThemeFontFamily.objects.create(
            fonts=fonts, role="heading", font_family="Roboto"
        )
        assert family.font_family == "Roboto"
        assert family.css_value == "'Roboto', sans-serif"

    def test_str(self, theme):
        fonts = DaisyUIThemeFonts.objects.create(theme=theme)
        assert "fonts" in str(fonts).lower()

    def test_defaults(self, theme):
        fonts = DaisyUIThemeFonts.objects.create(theme=theme)
        family = DaisyUIThemeFontFamily.objects.create(fonts=fonts, role="body")
        assert family.font_family == "Inter"
        assert family.generic_font_family == "sans-serif"
        assert fonts.base_font_size == "1rem"
        assert fonts.line_height == 1.5

    def test_clean_unsaved_family_does_not_raise(self):
        family = DaisyUIThemeFontFamily(role="body", font_family="Inter")
        assert family.fonts_id is None
        family.clean()

    def test_clean_rejects_duplicate_role(self, theme):
        fonts = DaisyUIThemeFonts.objects.create(theme=theme)
        DaisyUIThemeFontFamily.objects.create(fonts=fonts, role="body")
        duplicate = DaisyUIThemeFontFamily(fonts=fonts, role="body")
        with pytest.raises(ValidationError):
            duplicate.clean()

    def test_clean_requires_name_for_custom(self, theme):
        fonts = DaisyUIThemeFonts.objects.create(theme=theme)
        custom = DaisyUIThemeFontFamily(fonts=fonts, role="custom", name="")
        with pytest.raises(ValidationError):
            custom.clean()

    def test_css_value_includes_fallbacks(self, theme):
        fonts = DaisyUIThemeFonts.objects.create(theme=theme)
        family = DaisyUIThemeFontFamily.objects.create(
            fonts=fonts, role="body", font_family="Inter"
        )
        fallback = DaisyUIThemeFontFallback.objects.create(
            font_family=family, name="Roboto"
        )
        assert str(fallback) == "Roboto"
        assert fallback.css_value == "'Roboto'"
        assert family.css_value == "'Inter', 'Roboto', sans-serif"


class TestDaisyUIThemeFontCDN:
    def test_create(self, theme):
        cdn = DaisyUIThemeFontCDN.objects.create(
            theme=theme,
            url="https://fonts.googleapis.com/css2?family=Inter",
            label="Google Fonts - Inter",
        )
        assert cdn.url == "https://fonts.googleapis.com/css2?family=Inter"
        assert cdn.label == "Google Fonts - Inter"

    def test_str_with_label(self, theme):
        cdn = DaisyUIThemeFontCDN.objects.create(
            theme=theme,
            url="https://example.com/font.css",
            label="My Font",
        )
        assert str(cdn) == "My Font"

    def test_str_without_label(self, theme):
        cdn = DaisyUIThemeFontCDN.objects.create(
            theme=theme,
            url="https://example.com/font.css",
        )
        assert str(cdn) == "https://example.com/font.css"

    def test_multiple_cdns_per_theme(self, theme):
        DaisyUIThemeFontCDN.objects.create(
            theme=theme, url="https://example.com/font1.css"
        )
        DaisyUIThemeFontCDN.objects.create(
            theme=theme, url="https://example.com/font2.css"
        )
        assert theme.font_cdns.count() == 2

    def test_blank_label(self, theme):
        cdn = DaisyUIThemeFontCDN.objects.create(
            theme=theme, url="https://example.com/font.css", label=""
        )
        assert cdn.label == ""


class TestDaisyUIMenu:
    def test_create(self):
        menu = DaisyUIMenu.objects.create(name="Main Nav", layout="navbar")
        assert menu.name == "Main Nav"
        assert menu.layout == "navbar"

    def test_str(self):
        menu = DaisyUIMenu.objects.create(name="Footer")
        assert str(menu) == "Footer"

    def test_unique_name(self):
        DaisyUIMenu.objects.create(name="Nav")
        with pytest.raises(IntegrityError):
            DaisyUIMenu.objects.create(name="Nav")

    def test_layout_choices(self):
        for layout in ["navbar", "footer", "sidebar", "horizontal", "vertical"]:
            menu = DaisyUIMenu.objects.create(name=f"Menu {layout}", layout=layout)
            assert menu.layout == layout

    def test_body_blocks(self):
        menu = DaisyUIMenu.objects.create(name="Blocks")
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
        menu.refresh_from_db()
        assert menu.body[0].block_type == "link"
        assert menu.body[0].value["destination"][0].value == "https://example.com"

    def test_theme_and_item_design(self, theme):
        menu = DaisyUIMenu.objects.create(name="Themed", menu_theme=theme)
        assert menu.get_theme() == theme
        menu.item_design = [
            ("item", {"typography": {"text_color": "text-base-content"}})
        ]
        menu.save()
        menu.refresh_from_db()
        assert "text-base-content" in menu.get_item_css()

    def test_get_theme_falls_back_to_default(self, theme):
        menu = DaisyUIMenu.objects.create(name="Default theme")
        assert menu.get_theme() == theme


class TestThemeBackgroundIntegration:
    def test_theme_has_background(self, theme):
        bg = DaisyUIThemeBackground.objects.create(theme=theme)
        assert theme.background.first() == bg

    def test_theme_has_fonts(self, theme):
        fonts = DaisyUIThemeFonts.objects.create(theme=theme)
        assert theme.fonts.first() == fonts

    def test_theme_has_font_cdns(self, theme):
        DaisyUIThemeFontCDN.objects.create(
            theme=theme, url="https://example.com/font.css"
        )
        DaisyUIThemeFontCDN.objects.create(
            theme=theme, url="https://example.com/font2.css"
        )
        assert theme.font_cdns.count() == 2
