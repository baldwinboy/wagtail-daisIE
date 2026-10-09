import pytest

from wagtail_daisIE.base_blocks.fields import (
    FontFamilyChoiceBlock,
    resolve_font_family_theme,
)
from wagtail_daisIE.base_blocks.utils import build_font_family_choices
from wagtail_daisIE.context import (
    reset_current_theme,
    set_current_theme,
    theme_from_instance,
)
from wagtail_daisIE.menus.models import DaisyUIMenu
from wagtail_daisIE.models import (
    DaisyUITheme,
    DaisyUIThemeFontFamily,
    DaisyUIThemeFonts,
)
from wagtail_daisIE.test.models import WidgetIndexPage


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

        # The admin hooks set the theme for the page/snippet being
        # created/edited; the picker follows it instead of the default.
        other = DaisyUITheme.objects.create(name="fonts-theme-other")
        token = set_current_theme(other)
        try:
            assert resolve_font_family_theme() == other
        finally:
            reset_current_theme(token)

        # ``theme_from_instance`` reads page/menu themes but treats model
        # classes (passed by the ``before_create_*`` hooks) as no theme.
        page = WidgetIndexPage(title="Index", page_theme=theme_with_font)
        assert theme_from_instance(page) == theme_with_font
        assert theme_from_instance(DaisyUIMenu) is None
        assert theme_from_instance(None) is None
