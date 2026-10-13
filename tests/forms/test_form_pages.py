from types import SimpleNamespace

import pytest

from django import forms
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from django.http import QueryDict
from django.utils.datastructures import MultiValueDict

from wagtail_daisIE.dynamic.registry import reset_context_models
from wagtail_daisIE.forms.blocks import (
    FormFieldBlock,
    duplicate_field_names,
    placed_field_names,
)
from wagtail_daisIE.forms.builder import DaisyUIFormBuilder
from wagtail_daisIE.forms.fields import (
    DaisieFileField,
    DaisieFormField,
    InstanceModelSelect,
    ModelFieldSelect,
    MultipleFileInput,
)
from wagtail_daisIE.forms.models import DaisieFormPage
from wagtail_daisIE.forms.registry import (
    FIELD_TYPE_MAX_LENGTH,
    get_default_upload_handler,
    get_form_field_type,
    get_form_field_type_choices,
    get_form_field_types,
    is_upload_field_type,
    reset_form_field_types,
)
from wagtail_daisIE.forms.widgets_file import AttachmentsFileInput, ImageFileInput
from wagtail_daisIE.widgets import DaisieAutocompleteSelectMultiple


def _tag_choices(field, context):
    return [("a", "Alpha"), ("b", "Bravo")]


def _store_file(*, page, form, field, file, request=None):
    return f"stored:{file.name}"


class _MultipleUploadField(forms.FileField):
    def clean(self, data, initial=None):
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [super().clean(item, initial) for item in data]
        return [super().clean(data, initial)]


def _build_multiple_file_field(form_field, options):
    return _MultipleUploadField(required=options.get("required", False))


@pytest.fixture(autouse=True)
def _field_type_registry(settings):
    settings.WAGTAIL_DAISIE_FORM_FIELD_TYPES = {
        "file": {
            "label": "File upload",
            "field": "django.forms.FileField",
            "widget": "django.forms.ClearableFileInput",
            "css": "file-input w-full",
            "is_upload": True,
            "handler": _store_file,
        },
        "multifile": {
            "label": "Multiple files",
            "field": _build_multiple_file_field,
            "is_upload": True,
            "handler": _store_file,
        },
        "upload": {
            "label": "Upload",
            "display": "attachments",
            "multiple": True,
            "is_upload": True,
            "handler": _store_file,
        },
        "image": {
            "label": "Image",
            "display": "image",
            "is_upload": True,
            "handler": _store_file,
        },
        "autocomplete": {
            "label": "Autocomplete",
            "field": "django.forms.MultipleChoiceField",
            "widget": "wagtail_daisIE.widgets.DaisieAutocompleteSelectMultiple",
            "choices": True,
        },
        "tags": {
            "label": "Tags",
            "field": "django.forms.MultipleChoiceField",
            "widget": "wagtail_daisIE.widgets.DaisieAutocompleteSelectMultiple",
            "choices": _tag_choices,
        },
    }
    settings.WAGTAIL_DAISIE_FORM_UPLOAD_HANDLER = ""
    reset_form_field_types()
    yield
    reset_form_field_types()


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

    def test_registered_field_type_is_built_from_registry(self):
        field = _FakeField()
        field.field_type = "file"
        create = DaisyUIFormBuilder([]).get_create_field_function("file")
        result = create(field, {"label": "Photo", "required": False})
        assert isinstance(result, forms.FileField)
        assert "file-input" in result.widget.attrs["class"]

        field = _FakeField()
        field.field_type = "autocomplete"
        field.choices = "5-10/5"
        create = DaisyUIFormBuilder([]).get_create_field_function("autocomplete")
        result = create(field, {"required": False})
        assert isinstance(result, forms.MultipleChoiceField)
        assert isinstance(result.widget, DaisieAutocompleteSelectMultiple)
        assert list(result.choices) == [("5", "5"), ("10", "10")]

        field = _FakeField()
        field.field_type = "tags"
        create = DaisyUIFormBuilder([]).get_create_field_function("tags")
        result = create(field, {"required": False})
        assert list(result.choices) == [("a", "Alpha"), ("b", "Bravo")]

    def test_registry_factory_is_supported(self):
        field = _FakeField()
        field.field_type = "multifile"
        create = DaisyUIFormBuilder([]).get_create_field_function("multifile")
        result = create(field, {"required": False})
        assert isinstance(result, _MultipleUploadField)

    def test_upload_type_without_field_defaults_to_daisie_file_field(self):
        field = _FakeField()
        field.field_type = "upload"
        create = DaisyUIFormBuilder([]).get_create_field_function("upload")
        result = create(field, {"required": False})
        assert isinstance(result, DaisieFileField)
        assert result.multiple is True
        assert isinstance(result.widget, AttachmentsFileInput)

    def test_image_display_selects_image_widget(self):
        field = _FakeField()
        field.field_type = "image"
        create = DaisyUIFormBuilder([]).get_create_field_function("image")
        result = create(field, {"required": False})
        assert isinstance(result, DaisieFileField)
        assert result.multiple is False
        assert isinstance(result.widget, ImageFileInput)

    def test_widget_design_is_threaded_onto_the_widget(self):
        class _DesignedUpload(_FakeField):
            def get_widget_design(self):
                return {
                    "tray_css": "gap-4",
                    "item_css": "rounded-full",
                    "render": "icon",
                    "fallback": "initials",
                }

        field = _DesignedUpload()
        field.field_type = "upload"
        create = DaisyUIFormBuilder([]).get_create_field_function("upload")
        widget = create(field, {"required": False}).widget
        assert widget.design == {
            "tray_css": "gap-4",
            "item_css": "rounded-full",
            "render": "icon",
            "fallback": "initials",
        }


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

        # M2M/taggit values are set after save rather than passed to model().
        from django.contrib.auth.models import Group

        group = Group.objects.create(name="testers")

        class _GroupForm(_FakeForm):
            cleaned_data = {
                "display_name": "Dan",
                "username": "dan",
                "email": "d@e.com",
                "groups": [group.pk],
            }

        page = _DummyPage()
        page.require_approval = False
        third = DaisieFormPage.create_instance_from_submission(page, _GroupForm())
        assert third is not None
        assert list(third.groups.values_list("name", flat=True)) == ["testers"]

        # Edit mode updates the bound instance in place.
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create(username="carol")

        class _UpdateForm(_FakeForm):
            cleaned_data = {
                "display_name": "Carol",
                "username": "carol",
                "email": "c@e.com",
            }

        updated = DaisieFormPage.update_instance_from_submission(
            _DummyPage(), _UpdateForm(), user
        )
        assert updated.pk == user.pk
        assert user.first_name == "Carol"


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


class TestFieldTypeRegistry:
    def test_choices_include_defaults_and_registered_types(self):
        choices = dict(get_form_field_type_choices())
        assert str(choices["singleline"]) == "Single line text"
        assert "file" in choices and "multifile" in choices
        assert "autocomplete" in choices and "tags" in choices

    def test_lookup_and_upload_flag(self):
        assert get_form_field_type("file") is not None
        assert get_form_field_type("missing") is None
        assert is_upload_field_type("file") is True
        assert is_upload_field_type("singleline") is False
        assert is_upload_field_type("missing") is False

    def test_keys_fit_the_field_type_column(self):
        model_max = DaisieFormField._meta.get_field("field_type").max_length
        assert model_max == FIELD_TYPE_MAX_LENGTH
        for key in get_form_field_types():
            assert len(key) <= FIELD_TYPE_MAX_LENGTH

    def test_upload_spec_parses_display_and_multiple(self, settings):
        settings.WAGTAIL_DAISIE_FORM_FIELD_TYPES = {
            "files": {
                "label": "Files",
                "display": "attachments",
                "multiple": True,
                "is_upload": True,
                "handler": _store_file,
            }
        }
        reset_form_field_types()
        spec = get_form_field_type("files")
        assert spec.display == "attachments"
        assert spec.multiple is True

    def test_unknown_display_warns_and_falls_back(self, settings, caplog):
        settings.WAGTAIL_DAISIE_FORM_FIELD_TYPES = {"x": {"display": "nope"}}
        reset_form_field_types()
        with caplog.at_level("WARNING"):
            get_form_field_types()
        assert "unknown display" in caplog.text
        assert get_form_field_type("x").display == "default"

    def test_validators_resolve_callables_and_paths(self, settings):
        settings.WAGTAIL_DAISIE_FORM_FIELD_TYPES = {
            "x": {
                "validators": [
                    _store_file,
                    "wagtail_daisIE.forms.registry.get_default_upload_handler",
                ],
                "collection_validators": [_tag_choices],
            }
        }
        reset_form_field_types()
        spec = get_form_field_type("x")
        assert spec.resolved_validators == [_store_file, get_default_upload_handler]
        assert spec.resolved_collection_validators == [_tag_choices]

    def test_unresolvable_validator_fails_closed(self, settings):
        settings.WAGTAIL_DAISIE_FORM_FIELD_TYPES = {
            "x": {"validators": ["not.a.real.validator"]}
        }
        reset_form_field_types()
        with pytest.raises(ImproperlyConfigured):
            _ = get_form_field_type("x").resolved_validators

    def test_overlong_key_warns(self, settings, caplog):
        settings.WAGTAIL_DAISIE_FORM_FIELD_TYPES = {
            "a" * (FIELD_TYPE_MAX_LENGTH + 1): {
                "field": "django.forms.FileField",
                "is_upload": True,
                "handler": _store_file,
            }
        }
        reset_form_field_types()
        with caplog.at_level("WARNING"):
            get_form_field_types()
        assert "longer than" in caplog.text


class _UploadField:
    label = "Photo"
    clean_name = "photo"
    field_type = "file"
    is_upload = True


class _MultiUploadField(_UploadField):
    field_type = "multifile"


class _UploadPage:
    instance_model = ""
    _daisie_request = None

    def __init__(self, fields):
        self._fields = fields

    def get_form_fields(self):
        return self._fields

    get_upload_handler = DaisieFormPage.get_upload_handler
    get_submission_form_data = DaisieFormPage.get_submission_form_data
    _store_upload = DaisieFormPage._store_upload


def _upload_form(value):
    return SimpleNamespace(cleaned_data={"photo": value, "title": "x"})


class TestUploadSubmission:
    def test_handler_result_is_stored_in_form_data(self):
        page = _UploadPage([_UploadField()])
        data = page.get_submission_form_data(
            _upload_form(SimpleUploadedFile("a.txt", b"hi"))
        )
        assert data == {"photo": "stored:a.txt", "title": "x"}

    def test_empty_value_skips_handler(self):
        page = _UploadPage([_UploadField()])
        assert page.get_submission_form_data(_upload_form(None))["photo"] is None

    def test_multiple_files_call_handler_per_file(self):
        page = _UploadPage([_MultiUploadField()])
        data = page.get_submission_form_data(
            _upload_form(
                [
                    SimpleUploadedFile("a.txt", b"a"),
                    SimpleUploadedFile("b.txt", b"b"),
                ]
            )
        )
        assert data["photo"] == ["stored:a.txt", "stored:b.txt"]

    def test_mixed_reference_and_upload_only_stores_new_files(self):
        page = _UploadPage([_MultiUploadField()])
        data = page.get_submission_form_data(
            _upload_form(["stored:a.txt", SimpleUploadedFile("b.txt", b"b")])
        )
        assert data["photo"] == ["stored:a.txt", "stored:b.txt"]

    def test_reference_string_is_not_sent_to_handler(self):
        page = _UploadPage([_UploadField()])
        data = page.get_submission_form_data(_upload_form("stored:x.txt"))
        assert data["photo"] == "stored:x.txt"

    def test_missing_handler_raises(self, settings):
        settings.WAGTAIL_DAISIE_FORM_FIELD_TYPES = {
            "file": {
                "label": "File upload",
                "field": "django.forms.FileField",
                "is_upload": True,
            }
        }
        reset_form_field_types()
        page = _UploadPage([_UploadField()])
        with pytest.raises(ImproperlyConfigured):
            page.get_submission_form_data(
                _upload_form(SimpleUploadedFile("a.txt", b"hi"))
            )

    def test_global_default_handler_is_used(self, settings):
        settings.WAGTAIL_DAISIE_FORM_FIELD_TYPES = {
            "file": {
                "label": "File upload",
                "field": "django.forms.FileField",
                "is_upload": True,
            }
        }
        settings.WAGTAIL_DAISIE_FORM_UPLOAD_HANDLER = _store_file
        reset_form_field_types()
        page = _UploadPage([_UploadField()])
        data = page.get_submission_form_data(
            _upload_form(SimpleUploadedFile("a.txt", b"hi"))
        )
        assert data["photo"] == "stored:a.txt"

    def test_page_handler_override_is_used(self):
        class _OverridePage(_UploadPage):
            def get_upload_handler(self, field, form=None):
                return lambda **kwargs: "overridden"

        page = _OverridePage([_UploadField()])
        data = page.get_submission_form_data(
            _upload_form(SimpleUploadedFile("a.txt", b"hi"))
        )
        assert data["photo"] == "overridden"


class TestDaisieFileField:
    def test_single_returns_file(self):
        upload = SimpleUploadedFile("a.txt", b"hi")
        assert DaisieFileField().clean(upload) is upload

    def test_multiple_returns_list(self):
        a = SimpleUploadedFile("a.txt", b"a")
        b = SimpleUploadedFile("b.txt", b"b")
        assert DaisieFileField(multiple=True).clean([a, b]) == [a, b]

    def test_multiple_empty_not_required(self):
        assert DaisieFileField(multiple=True, required=False).clean([]) == []

    def test_multiple_required_empty_raises(self):
        with pytest.raises(ValidationError):
            DaisieFileField(multiple=True, required=True).clean([])

    def test_multiple_forces_multi_widget(self):
        assert isinstance(DaisieFileField(multiple=True).widget, MultipleFileInput)

    def test_per_file_validator_runs_per_item(self):
        seen = []
        field = DaisieFileField(multiple=True, validators=[seen.append])
        a = SimpleUploadedFile("a.txt", b"a")
        b = SimpleUploadedFile("b.txt", b"b")
        field.clean([a, b])
        assert seen == [a, b]

    def test_per_file_validator_error_surfaces(self):
        def reject(file):
            raise ValidationError("nope")

        with pytest.raises(ValidationError):
            DaisieFileField(validators=[reject]).clean(
                SimpleUploadedFile("a.txt", b"a")
            )

    def test_collection_validator_receives_list(self):
        seen = []
        field = DaisieFileField(multiple=True, collection_validators=[seen.append])
        a = SimpleUploadedFile("a.txt", b"a")
        field.clean([a])
        assert seen == [[a]]

    def test_reference_strings_pass_through(self):
        seen = []
        field = DaisieFileField(multiple=True, validators=[seen.append])
        result = field.clean(["stored:a.txt", SimpleUploadedFile("b.txt", b"b")])
        assert result[0] == "stored:a.txt"
        assert isinstance(result[1], UploadedFile)
        assert len(seen) == 1 and isinstance(seen[0], UploadedFile)


class TestFileWidgets:
    def test_attachments_merges_new_files_and_existing_refs(self):
        widget = AttachmentsFileInput()
        data = QueryDict("photo-existing=stored:a.txt&photo-existing=stored:b.txt")
        files = MultiValueDict({"photo": [SimpleUploadedFile("c.txt", b"c")]})
        value = widget.value_from_datadict(data, files, "photo")
        assert value[0].name == "c.txt"
        assert value[1:] == ["stored:a.txt", "stored:b.txt"]

    def test_attachments_empty_value(self):
        widget = AttachmentsFileInput()
        assert (
            widget.value_from_datadict(QueryDict(""), MultiValueDict(), "photo") == []
        )

    def test_attachments_not_omitted_when_existing_present(self):
        widget = AttachmentsFileInput()
        assert (
            widget.value_omitted_from_data(
                QueryDict("photo-existing=stored:a.txt"), MultiValueDict(), "photo"
            )
            is False
        )

    def test_attachments_omitted_when_empty(self):
        widget = AttachmentsFileInput()
        assert (
            widget.value_omitted_from_data(QueryDict(""), MultiValueDict(), "photo")
            is True
        )

    def test_attachments_context_lists_existing(self):
        context = AttachmentsFileInput().get_context("photo", ["a", "b"], {})
        assert context["existing"] == ["a", "b"]

    def test_attachments_render_includes_existing_inputs_and_template(self):
        html = AttachmentsFileInput().render("photo", ["stored:a.txt"], attrs={})
        assert 'name="photo-existing"' in html
        assert "stored:a.txt" in html
        assert "data-daisie-file-template" in html

    def test_image_widget_is_clearable(self):
        assert isinstance(ImageFileInput(), forms.ClearableFileInput)

    def test_image_widget_renders(self):
        html = ImageFileInput().render("photo", None, attrs={})
        assert "data-daisie-file-image" in html
        assert "data-daisie-file-image-preview" in html

    def test_attachments_render_applies_widget_design(self):
        widget = AttachmentsFileInput()
        widget.design = {
            "tray_css": "gap-4",
            "item_css": "rounded-full",
            "render": "icon",
            "fallback": "initials",
        }
        html = widget.render("photo", None, attrs={})
        assert "gap-4" in html
        assert "rounded-full" in html
        assert 'data-daisie-file-render="icon"' in html
        assert 'data-daisie-file-fallback="initials"' in html


class TestFormFieldBlock:
    def test_bound_field_widget_and_unplaced_fields(self):
        form = _TitleForm()
        context = FormFieldBlock().get_context("title", {"form": form})
        assert context["bound_field"].name == "title"

        from wagtail_daisIE.context import (
            set_current_form_fields,
            set_current_model_fields,
        )
        from wagtail_daisIE.dynamic.registry import get_context_model

        # Only concrete, editable model fields are offered (never the pk).
        names = [f["name"] for f in get_context_model("member").form_fields()]
        assert "username" in names and "id" not in names

        set_current_form_fields(
            [
                {"name": "title", "label": "Title"},
                {"name": "notes", "label": "Notes"},
            ]
        )
        set_current_model_fields(
            [
                {"name": "title", "label": "Title"},
                {"name": "description", "label": "Description"},
            ]
        )
        try:
            form_select = FormFieldBlock().field.widget
            blank = str(form_select.render("field", ""))
            assert '<option value="" selected>' in blank
            assert 'value="title"' in blank and "Title" in blank
            chosen = str(form_select.render("field", "notes"))
            assert 'value="notes" selected' in chosen
            assert 'value="" selected' not in chosen

            model_select = ModelFieldSelect(empty_label="Use the field name")
            model_html = str(model_select.render("model_field", ""))
            assert '<option value="" selected>' in model_html
            assert 'value="title"' in model_html
            assert 'value="id"' not in model_html
            stale = str(model_select.render("model_field", "gone"))
            assert 'value="gone" selected' in stale

            hub = InstanceModelSelect()
            hub_attrs = hub.build_attrs({})
            assert hub_attrs["data-controller"] == "daisie-form-instance-model"
            assert (
                '"member"'
                in hub_attrs["data-daisie-form-instance-model-context-models-value"]
            )
        finally:
            set_current_form_fields(())
            set_current_model_fields(())

        from wagtail_daisIE.templatetags.wagtail_daisIE_tags import (
            unplaced_form_fields,
        )

        page = SimpleNamespace(get_placed_field_names=lambda: ["title"])
        assert [f.name for f in unplaced_form_fields(page, form)] == ["notes"]
        page = SimpleNamespace(get_placed_field_names=lambda: [])
        assert [f.name for f in unplaced_form_fields(page, form)] == ["title", "notes"]
