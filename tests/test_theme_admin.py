import pytest

from django.core.exceptions import ValidationError

from wagtail_daisIE.models import (
    BackgroundLayer,
    DaisyUIColorField,
    DaisyUITheme,
    DaisyUIThemeBackground,
)


pytestmark = pytest.mark.django_db


class TestDaisyUIColorField:
    def test_accepts_hex_and_hexa_equally(self):
        field = DaisyUIColorField(format="hexa")

        for value in ("#422ad5", "#422ad5ff", "#abc", "#abcd", "#AAbbCCAA"):
            assert field.clean(value, None) == value

    def test_rejects_malformed_colours(self):
        field = DaisyUIColorField(format="hexa")

        for value in ("#12345", "422ad5", "#gggggg", "#00000000ff", ""):
            with pytest.raises(ValidationError):
                field.clean(value, None)

    def test_background_layer_full_clean_accepts_hex(self):
        theme = DaisyUITheme.objects.create(
            name="fullclean-theme", color_scheme="light"
        )
        parent = DaisyUIThemeBackground.objects.create(theme=theme)
        layer = BackgroundLayer(background=parent, layer_type="solid", color="#422ad5")
        layer.full_clean()
        assert layer.color == "#422ad5"
