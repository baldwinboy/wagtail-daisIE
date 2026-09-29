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


class TestFontFamily:
    def test_resolve_theme_and_fill_choices(self, theme_with_font):
        assert resolve_font_family_theme() == theme_with_font
        assert ("heading", "Heading") in build_font_family_choices(theme_with_font)

        block = FontFamilyChoiceBlock()
        # Choices start empty and are filled per request, not at import time.
        assert ("heading", "Heading") not in block.field.choices
        block.get_form_state("")
        # The "" sentinel is the only value meaning "inherit from the theme".
        assert block.field.choices[0] == ("", "Default")
        assert ("heading", "Heading") in block.field.choices
