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


def _child(block_type, value):
    return SimpleNamespace(block_type=block_type, value=value)


class _Body(list):
    pass


class TestPlacement:
    def test_placed_field_names_ignores_other_blocks(self):
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

    def test_placed_field_names_handles_empty_body(self):
        assert placed_field_names(None) == []
        assert placed_field_names([]) == []

    def test_duplicate_field_names(self):
        body = _Body(
            [
                _child("form_field", "title"),
                _child("header", {}),
                _child("form_field", "title"),
                _child("form_field", "notes"),
                _child("form_field", "title"),
                _child("form_field", "notes"),
            ]
        )
        assert duplicate_field_names(body) == ["title", "notes"]

    def test_no_duplicates(self):
        body = _Body([_child("form_field", "a"), _child("form_field", "b")])
        assert duplicate_field_names(body) == []


class _TitleForm(forms.Form):
    title = forms.CharField()
    notes = forms.CharField(required=False)


class TestFormFieldBlock:
    def test_resolves_bound_field_from_parent_context(self):
        form = _TitleForm()
        context = FormFieldBlock().get_context("title", {"form": form})
        assert context["bound_field"].name == "title"

    def test_unknown_field_has_no_bound_field(self):
        context = FormFieldBlock().get_context("nope", {"form": _TitleForm()})
        assert context["bound_field"] is None

    def test_no_form_in_context(self):
        assert FormFieldBlock().get_context("title", {})["bound_field"] is None

    def test_stored_value_is_rendered_in_the_admin_widget(self):
        block = FormFieldBlock()
        html = str(block.field.widget.render("title", "notes"))
        assert "notes" in html
        assert "data-daisie-form-field" in html


class TestUnplacedFormFields:
    def test_skips_placed_fields(self):
        from wagtail_daisIE.templatetags.wagtail_daisIE_tags import (
            unplaced_form_fields,
        )

        page = SimpleNamespace(get_placed_field_names=lambda: ["title"])
        remaining = unplaced_form_fields(page, _TitleForm())
        assert [field.name for field in remaining] == ["notes"]

    def test_without_placement_returns_every_field(self):
        from wagtail_daisIE.templatetags.wagtail_daisIE_tags import (
            unplaced_form_fields,
        )

        page = SimpleNamespace(get_placed_field_names=lambda: [])
        remaining = unplaced_form_fields(page, _TitleForm())
        assert [field.name for field in remaining] == ["title", "notes"]

    def test_without_form_returns_nothing(self):
        from wagtail_daisIE.templatetags.wagtail_daisIE_tags import (
            unplaced_form_fields,
        )

        assert unplaced_form_fields(SimpleNamespace(), None) == []
