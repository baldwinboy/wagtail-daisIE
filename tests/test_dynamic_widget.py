import pytest

from wagtail_daisIE.dynamic.forms import DynamicInstanceField
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
    def test_parses_int(self):
        field = DynamicInstanceField(required=False)
        assert field.to_python("3") == 3
        assert field.to_python(4) == 4

    def test_empty_value(self):
        field = DynamicInstanceField(required=False)
        assert field.to_python("") is None
        assert field.to_python(None) is None
        assert field.to_python("not a number") is None

    def test_has_changed(self):
        field = DynamicInstanceField(required=False)
        assert field.has_changed(1, "2") is True
        assert field.has_changed(1, "1") is False


class TestDynamicInstanceWidget:
    def test_context_exposes_object_id(self):
        from wagtail_daisIE.dynamic.forms import DynamicInstanceWidget

        widget = DynamicInstanceWidget()
        context = widget.get_context("binding-instance", 5, {})
        data = context["daisie_widget"]
        assert data["object_id"] == 5
        assert data["name"] == "binding-instance"

    def test_template_renders(self):
        from django.template.loader import render_to_string

        from wagtail_daisIE.dynamic.forms import DynamicInstanceWidget

        widget = DynamicInstanceWidget()
        context = widget.get_context("binding-object_id", 5, {})
        html = render_to_string(widget.template_name, context)
        assert "daisie-chooser" in html
        assert 'role="combobox"' in html
        assert 'role="listbox"' in html
        assert 'name="binding-object_id"' in html
        assert 'value="5"' in html
