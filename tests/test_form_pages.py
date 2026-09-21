import pytest

from wagtail_daisIE.dynamic.registry import reset_context_models
from wagtail_daisIE.forms.builder import DaisyUIFormBuilder
from wagtail_daisIE.forms.models import DaisieFormPage


class _FakeField:
    label = "Name"
    clean_name = "name"
    field_type = "singleline"
    required = True
    choices = ""
    default_value = ""
    help_text = ""


class TestBuilder:
    def test_singleline_gets_input_class(self):
        field = _FakeField()
        result = DaisyUIFormBuilder([]).create_singleline_field(field, {})
        assert "input" in result.widget.attrs["class"]

    def test_per_field_design_is_applied(self):
        class _DesignedField(_FakeField):
            def get_input_css(self):
                return "border-primary"

            def get_label_css(self):
                return "text-primary"

        result = DaisyUIFormBuilder([]).create_singleline_field(_DesignedField(), {})
        assert "border-primary" in result.widget.attrs["class"]
        assert result.input_css == "border-primary"
        assert result.label_css == "text-primary"

    def test_multiline_gets_textarea_class(self):
        field = _FakeField()
        field.field_type = "multiline"
        result = DaisyUIFormBuilder([]).create_multiline_field(field, {})
        assert "textarea" in result.widget.attrs["class"]

    def test_dropdown_gets_select_class(self):
        field = _FakeField()
        field.field_type = "dropdown"
        field.choices = "a,b"
        result = DaisyUIFormBuilder([]).create_dropdown_field(field, {})
        assert "select" in result.widget.attrs["class"]

    def test_checkbox_gets_checkbox_class(self):
        field = _FakeField()
        field.field_type = "checkbox"
        result = DaisyUIFormBuilder([]).create_checkbox_field(field, {})
        assert "checkbox" in result.widget.attrs["class"]


CONFIG = {"member": {"label": "Member", "model": "auth.User"}}


@pytest.fixture(autouse=True)
def _registry(settings):
    settings.WAGTAIL_DAISIE_CONTEXT_MODELS = CONFIG
    reset_context_models()
    yield
    reset_context_models()


class _DummyPage:
    instance_model = "member"
    require_approval = True
    approval_field = "is_active"

    def get_model_field_map(self):
        return {"display_name": "first_name"}


class _FakeForm:
    cleaned_data = {
        "display_name": "Ada",
        "username": "ada",
        "email": "ada@example.com",
        "ignored": "not a field",
    }


@pytest.mark.django_db
class TestInstanceCreation:
    def test_creates_instance_with_approval(self):
        result = DaisieFormPage.create_instance_from_submission(
            _DummyPage(), _FakeForm()
        )
        assert result is not None
        assert result.username == "ada"
        assert result.first_name == "Ada"
        assert result.is_active is False

    def test_without_approval_is_active(self):
        page = _DummyPage()
        page.require_approval = False
        result = DaisieFormPage.create_instance_from_submission(page, _FakeForm())
        assert result.is_active is True

    def test_unknown_model_returns_none(self):
        page = _DummyPage()
        page.instance_model = "missing"
        assert DaisieFormPage.create_instance_from_submission(page, _FakeForm()) is None

    def test_unmapped_missing_fields_are_skipped(self):
        result = DaisieFormPage.create_instance_from_submission(
            _DummyPage(), _FakeForm()
        )
        assert not hasattr(result, "ignored")
