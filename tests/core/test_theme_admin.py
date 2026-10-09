import pytest

from django.core.exceptions import ValidationError
from django.urls import reverse
from wagtail.models import Page

from wagtail_daisIE.models import (
    BackgroundLayer,
    DaisyUIColorField,
    DaisyUITheme,
    DaisyUIThemeBackground,
)


pytestmark = pytest.mark.django_db


class TestDaisyUIColorField:
    def test_accepts_and_rejects_colours(self):
        field = DaisyUIColorField(format="hexa")
        for value in ("#422ad5", "#422ad5ff", "#abc", "#abcd", "#AAbbCCAA"):
            assert field.clean(value, None) == value
        for value in ("#12345", "422ad5", "#gggggg", "#00000000ff", ""):
            with pytest.raises(ValidationError):
                field.clean(value, None)

    def test_background_layer_full_clean_accepts_hex(self):
        theme = DaisyUITheme.objects.create(
            name="fullclean-theme", color_scheme="light"
        )
        parent = DaisyUIThemeBackground.objects.create(theme=theme)
        # full_clean() accepting the value proves the hex validator is wired.
        BackgroundLayer(
            background=parent, layer_type="solid", color="#422ad5"
        ).full_clean()


class TestPageCreateAdmin:
    def test_create_form_renders(self, admin_client):
        # Wagtail calls ``before_create_page(request, parent_page, page_class)``;
        # the registered hooks must accept that signature and render the form.
        response = admin_client.get(
            reverse(
                "wagtailadmin_pages:add",
                args=[
                    "wagtail_daisIE_test",
                    "widgetindexpage",
                    Page.get_first_root_node().pk,
                ],
            )
        )
        assert response.status_code == 200
