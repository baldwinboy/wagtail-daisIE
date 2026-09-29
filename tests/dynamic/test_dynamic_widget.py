import pytest

from wagtail_daisIE.dynamic.forms import DynamicInstanceField, DynamicInstanceWidget
from wagtail_daisIE.dynamic.registry import reset_context_models


pytestmark = pytest.mark.django_db

CONFIG = {
    "owner": {"label": "Owner", "model": "auth.User", "source": "request.user"},
}


@pytest.fixture(autouse=True)
def _registry(settings):
    settings.WAGTAIL_DAISIE_CONTEXT_MODELS = CONFIG
    reset_context_models()
    yield
    reset_context_models()


class TestDynamicInstanceField:
    def test_to_python_and_has_changed(self):
        field = DynamicInstanceField(required=False)
        for raw, expected in [
            ("3", 3),
            (4, 4),
            ("", None),
            (None, None),
            ("nope", None),
        ]:
            assert field.to_python(raw) == expected
        assert field.has_changed(1, "2") is True
        assert field.has_changed(1, "1") is False

    def test_widget_context_exposes_object_id(self):
        context = DynamicInstanceWidget().get_context("binding-instance", 5, {})
        data = context["daisie_widget"]
        assert data["object_id"] == 5
        assert data["name"] == "binding-instance"
