import pytest

from wagtail_daisIE.base_blocks.fields import (
    FontFamilyChoiceBlock,
    resolve_font_family_theme,
)
from wagtail_daisIE.base_blocks.utils import build_font_family_choices
from wagtail_daisIE.models import (
    DaisyUITheme,
    DaisyUIThemeFontFamily,
    DaisyUIThemeFonts,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def theme_with_font():
    theme = DaisyUITheme.objects.create(name="fonts-theme", default=True)
    fonts = DaisyUIThemeFonts.objects.create(theme=theme)
    DaisyUIThemeFontFamily.objects.create(
        fonts=fonts, role="heading", font_family="Marcellus"
    )
    return theme


class TestResolveFontFamilyTheme:
    def test_falls_back_to_default(self, theme_with_font):
        assert resolve_font_family_theme() == theme_with_font


class TestFontFamilyChoices:
    def test_role_value(self, theme_with_font):
        assert ("heading", "Heading") in build_font_family_choices(theme_with_font)

    def test_choice_block_fills_choices(self, theme_with_font):
        block = FontFamilyChoiceBlock()
        block.get_form_state("")
        assert ("heading", "Heading") in block.field.choices

    def test_unknown_theme_has_no_choices(self):
        assert build_font_family_choices(None) == []
