import pytest

from django.core.exceptions import ValidationError

from wagtail_daisIE.models import DaisyUIColorField


pytestmark = pytest.mark.django_db


class TestDaisyUIColorField:
    def test_accepts_and_rejects_colours(self):
        field = DaisyUIColorField(format="hexa")
        for value in ("#422ad5", "#422ad5ff", "#abc", "#abcd", "#AAbbCCAA"):
            assert field.clean(value, None) == value
        for value in ("#12345", "422ad5", "#gggggg", "#00000000ff", ""):
            with pytest.raises(ValidationError):
                field.clean(value, None)
