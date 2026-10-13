"""Abstract form field with per-field design and model-field linking."""

from __future__ import annotations

import json

from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import EMPTY_VALUES
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, FieldRowPanel
from wagtail.contrib.forms.models import AbstractFormField
from wagtail.fields import StreamField

from ..base_blocks.css import build_design_css
from ..base_blocks.design import TypographyDesignBlock
from ..base_blocks.input_widget import InputWidgetDesignBlock
from ..context import get_current_model_fields
from ..dynamic.registry import get_context_models
from .registry import (
    FIELD_TYPE_MAX_LENGTH,
    get_form_field_type_choices,
    is_upload_field_type,
)


class DaisieFieldSelect(forms.Select):
    """A ``Select`` whose options are the fields available for the current
    admin request (resolved lazily from a contextvar).

    A blank option is always rendered first so an unset value never falls back
    to the browser's "select the first option" behaviour. A stored value that is
    no longer available is kept as a selected ``(missing)`` option rather than
    being silently dropped.
    """

    empty_label = ""

    def __init__(self, attrs=None, choices=(), empty_label=""):
        super().__init__(attrs, choices)
        self.empty_label = empty_label

    def get_field_choices(self):
        """Return ``[{"name", "label"}]``; overridden by subclasses."""
        raise NotImplementedError

    def optgroups(self, name, value, attrs=None):
        if self.choices:
            return super().optgroups(name, value, attrs)

        fields = self.get_field_choices()
        values = value if isinstance(value, (list, tuple)) else [value]
        current = next((str(item) for item in values if item not in (None, "")), "")

        options = [self.create_option(name, "", self.empty_label, not current, 0)]
        known = not current
        index = 1
        for field in fields:
            selected = field["name"] == current
            known = known or selected
            options.append(
                self.create_option(
                    name,
                    field["name"],
                    field["label"] or field["name"],
                    selected,
                    index,
                )
            )
            index += 1

        if not known:
            options.append(
                self.create_option(name, current, f"{current} (missing)", True, index)
            )
        return [(None, options, 0)]


class ModelFieldSelect(DaisieFieldSelect):
    """The "Model field" select, populated from the page's bound model."""

    def get_field_choices(self):
        return get_current_model_fields()

    @property
    def media(self):
        return forms.Media(js=["wagtail_daisIE/js/forms_admin.js"])

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["data-controller"] = "daisie-form-model-field"
        attrs["data-daisie-form-model-field-empty-value"] = str(self.empty_label)
        return attrs


class InstanceModelSelect(forms.Select):
    """The "Model to create" select, wired to the form-fields Stimulus hub.

    Carries the editable fields of every configured context model so the
    "Model field" selects and the help panel can update when the chosen model
    changes without a page reload.
    """

    @property
    def media(self):
        return forms.Media(js=["wagtail_daisIE/js/forms_admin.js"])

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["data-controller"] = "daisie-form-instance-model"
        attrs["data-action"] = "change->daisie-form-instance-model#refresh"
        attrs["data-daisie-form-instance-model-context-models-value"] = json.dumps(
            {key: config.form_fields() for key, config in get_context_models().items()}
        )
        attrs["data-daisie-form-instance-model-daisie-form-model-field-outlet"] = (
            '[data-controller~="daisie-form-model-field"]'
        )
        return attrs


class MultipleFileInput(forms.FileInput):
    """A ``FileInput`` that submits every selected file.

    Django's ``FileInput`` already supports this via ``allow_multiple_selected``
    (it adds the ``multiple`` attribute and reads ``files.getlist(name)``).
    """

    allow_multiple_selected = True


class DaisieFileField(forms.FileField):
    """A single or multiple file upload with app-supplied validation.

    ``validators`` run once per uploaded file (edit-mode reference strings are
    passed through untouched); ``collection_validators`` run once on the final
    value. Both are supplied by the consuming app — the package ships no
    validators and never imports an imaging library.
    """

    def __init__(
        self,
        *,
        multiple=False,
        validators=(),
        collection_validators=(),
        **kwargs,
    ):
        self.multiple = multiple
        self.collection_validators = list(collection_validators)
        existing = list(kwargs.pop("validators", None) or [])
        kwargs["validators"] = [*existing, *validators]
        if multiple and "widget" not in kwargs:
            kwargs["widget"] = MultipleFileInput
        super().__init__(**kwargs)

    @staticmethod
    def _is_upload(value):
        return isinstance(value, UploadedFile)

    @staticmethod
    def _as_list(data):
        if data is False or data in EMPTY_VALUES:
            return []
        if isinstance(data, (list, tuple)):
            return list(data)
        return [data]

    def _run_collection_validators(self, value):
        for validator in self.collection_validators:
            validator(value)

    def clean(self, data, initial=None):
        if not self.multiple:
            value = super().clean(data, initial)
            self._run_collection_validators(value)
            return value
        files = self._as_list(data)
        self.validate(files)
        cleaned = [
            super(DaisieFileField, self).clean(item, None)
            if self._is_upload(item)
            else item
            for item in files
        ]
        self._run_collection_validators(cleaned)
        return cleaned

    def bound_data(self, data, initial):
        if self.multiple:
            # Existing references survive a re-render after a validation error
            # (files cannot be repopulated client-side, so they are dropped).
            return [item for item in self._as_list(data) if not self._is_upload(item)]
        return super().bound_data(data, initial)


class DaisieFormField(AbstractFormField):
    """A Wagtail form field that can be styled and linked to a model field.

    The available field types are Wagtail's defaults plus every type registered
    in ``WAGTAIL_DAISIE_FORM_FIELD_TYPES`` (see
    :mod:`wagtail_daisIE.forms.registry`).
    """

    field_type = models.CharField(
        verbose_name=_("field type"),
        max_length=FIELD_TYPE_MAX_LENGTH,
        choices=get_form_field_type_choices,
    )
    field_type.required_on_save = True
    model_field = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name=_("Model field"),
        help_text=_(
            "The model field this input is stored in. Defaults to the field name."
        ),
    )
    input_design = StreamField(
        [("design", InputWidgetDesignBlock())],
        blank=True,
        max_num=1,
        use_json_field=True,
        verbose_name=_("Input design"),
    )
    label_design = StreamField(
        [("design", TypographyDesignBlock())],
        blank=True,
        max_num=1,
        use_json_field=True,
        verbose_name=_("Label design"),
    )

    panels = [
        *AbstractFormField.panels,
        FieldPanel(
            "model_field",
            widget=ModelFieldSelect(empty_label=_("Use the field name")),
        ),
        FieldRowPanel(
            [
                FieldPanel("input_design"),
                FieldPanel("label_design"),
            ],
            heading=_("Design"),
            classname="collapsed",
        ),
    ]

    class Meta(AbstractFormField.Meta):
        abstract = True

    @property
    def is_upload(self):
        """Whether this field accepts a file upload."""
        return is_upload_field_type(self.field_type)

    def get_input_css(self):
        return build_design_css(
            self.input_design[0].value if self.input_design else None
        )

    def get_widget_design(self):
        """Return the tray/item/render/fallback design for the upload widget."""
        value = self.input_design[0].value if self.input_design else None
        value = value or {}
        return {
            "tray_css": build_design_css(value.get("tray")),
            "item_css": build_design_css(value.get("item")),
            "render": value.get("render") or "thumbnail",
            "fallback": value.get("fallback") or "icon",
        }

    def get_label_css(self):
        return build_design_css(
            self.label_design[0].value if self.label_design else None
        )
