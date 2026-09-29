from types import SimpleNamespace

import pytest

from django import forms

from wagtail_daisIE.dynamic.registry import reset_context_models
from wagtail_daisIE.forms.blocks import (
    FormFieldBlock,
    duplicate_field_names,
    placed_field_names,
)
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
    def test_widget_class_per_field_type(self):
        for field_type, method, expected_class in [
            ("singleline", "create_singleline_field", "input"),
            ("multiline", "create_multiline_field", "textarea"),
            ("dropdown", "create_dropdown_field", "select"),
            ("checkbox", "create_checkbox_field", "checkbox"),
        ]:
            field = _FakeField()
            field.field_type = field_type
            if field_type == "dropdown":
                field.choices = "a,b"
            result = getattr(DaisyUIFormBuilder([]), method)(field, {})
            assert expected_class in result.widget.attrs["class"]

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


class _FakeForm2(_FakeForm):
    cleaned_data = {
        "display_name": "Bob",
        "username": "bob",
        "email": "bob@example.com",
    }


@pytest.mark.django_db
class TestInstanceCreation:
    def test_creates_instance_with_and_without_approval(self):
        result = DaisieFormPage.create_instance_from_submission(
            _DummyPage(), _FakeForm()
        )
        assert result is not None
        assert result.username == "ada"
        assert result.first_name == "Ada"
        assert result.is_active is False

        page = _DummyPage()
        page.require_approval = False
        second = DaisieFormPage.create_instance_from_submission(page, _FakeForm2())
        assert second.username == "bob" and second.is_active is True


def _child(block_type, value):
    return SimpleNamespace(block_type=block_type, value=value)


class _Body(list):
    pass


class _TitleForm(forms.Form):
    title = forms.CharField()
    notes = forms.CharField(required=False)


class TestPlacement:
    def test_placed_and_duplicate_field_names(self):
        body = _Body(
            [
                _child("header", {"text": "Hi"}),
                _child("form_field", "title"),
                _child("form_field", ""),
                _child("rich_text", {"text": "…"}),
                _child("form_field", "description"),
            ]
        )
        assert placed_field_names(body) == ["title", "description"]

        duplicates = _Body(
            [
                _child("form_field", "title"),
                _child("header", {}),
                _child("form_field", "title"),
                _child("form_field", "notes"),
                _child("form_field", "title"),
                _child("form_field", "notes"),
            ]
        )
        assert duplicate_field_names(duplicates) == ["title", "notes"]


class TestFormFieldBlock:
    def test_bound_field_widget_and_unplaced_fields(self):
        form = _TitleForm()
        context = FormFieldBlock().get_context("title", {"form": form})
        assert context["bound_field"].name == "title"

        html = str(FormFieldBlock().field.widget.render("title", "notes"))
        assert "notes" in html and "data-daisie-form-field" in html

        from wagtail_daisIE.templatetags.wagtail_daisIE_tags import unplaced_form_fields

        page = SimpleNamespace(get_placed_field_names=lambda: ["title"])
        assert [f.name for f in unplaced_form_fields(page, form)] == ["notes"]
        page = SimpleNamespace(get_placed_field_names=lambda: [])
        assert [f.name for f in unplaced_form_fields(page, form)] == ["title", "notes"]
