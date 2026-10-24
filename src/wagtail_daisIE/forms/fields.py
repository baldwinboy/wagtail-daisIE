"""Abstract form field with per-field design and model-field linking."""

from __future__ import annotations

import json

from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import EMPTY_VALUES
from django.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractFormField
from wagtail.fields import StreamField

from ..base_blocks.css import (
    build_background_style,
    build_class,
    build_design_css,
)
from ..base_blocks.design import (
    ChoiceOptionsDesignBlock,
    SpacedDesignBlock,
    TypographyDesignBlock,
)
from ..base_blocks.input_widget import (
    InputWidgetDesignBlock,
    UploadWidgetDesignBlock,
)
from ..context import get_current_model_key
from ..dynamic.registry import get_context_models
from ..panels import PrefixedRulesPanel
from .registry import (
    FIELD_TYPE_MAX_LENGTH,
    get_form_field_type_choices,
    get_upload_field_type_keys,
    is_upload_field_type,
)


#: ``field_type`` values that use the "Choices" box.
CHOICE_FIELD_TYPES = [
    "checkboxes",
    "dropdown",
    "multiselect",
    "radio",
]

#: ``field_type`` values that use the "Default value" box.
DEFAULT_VALUE_FIELD_TYPES = [
    "dropdown",
    "radio",
]

#: ``field_type`` values rendered as a group of choice controls.
CHOICE_OPTIONS_FIELD_TYPES = [
    "checkboxes",
    "radio",
]


def field_option_choices(fields, value, empty_label, missing_label):
    """Return ``[(value, label)]`` for a model's editable fields.

    A blank option always comes first. A non-empty ``value`` that is no longer
    among the field names is appended as a ``missing_label`` option so a stored
    value is never silently dropped.
    """
    choices = [("", empty_label)]
    names = set()
    for field in fields:
        names.add(field["name"])
        choices.append((field["name"], field["label"] or field["name"]))
    if value and value not in names:
        choices.append((value, missing_label(value)))
    return choices


class DaisieFieldSelect(forms.Select):
    """... (docstring updated to drop the literal ``(missing)`` mention) ..."""

    empty_label = ""

    def __init__(self, attrs=None, choices=(), empty_label=""):
        super().__init__(attrs, choices)
        self.empty_label = empty_label

    def get_field_choices(self):
        raise NotImplementedError

    def missing_label(self, value):
        return _("%(value)s (not an available option)") % {"value": value}

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
                self.create_option(
                    name, current, self.missing_label(current), True, index
                )
            )
        return [(None, options, 0)]


class ModelFieldSelect(DaisieFieldSelect):
    """Render one "Model field" select per configured context model.

    Wagtail's ``w-rules`` controller reveals and enables the select whose model
    matches the page's ``instance_model`` field and leaves the others ``hidden``
    and ``disabled``, so only the active model's select is submitted. Every
    select — and its blank and ``(missing)`` options — is rendered server-side,
    so the option list has a single source of truth.
    """

    def missing_label(self, value):
        return _(
            "%(value)s (not a field on this model — choose a field "
            "or clear to use the field name)"
        ) % {"value": value}

    def render(self, name, value, attrs=None, renderer=None):
        attrs = self.build_attrs(self.attrs, attrs)
        value = "" if value is None else str(value)
        active_key = get_current_model_key()
        base_id = attrs.get("id") or f"id_{name}"

        selects = []
        for key, config in get_context_models().items():
            is_active = key == active_key
            select_attrs = dict(attrs)
            select_attrs["id"] = base_id if is_active else f"{base_id}_{key}"
            select_attrs["data-w-rules-target"] = "show enable"
            select_attrs["data-w-rules"] = json.dumps({"instance_model": [key]})
            if not is_active:
                select_attrs["hidden"] = True
                select_attrs["disabled"] = True

            widget = forms.Select(
                choices=field_option_choices(
                    config.form_fields(),
                    value,
                    self.empty_label,
                    self.missing_label,
                )
            )
            selects.append(widget.render(name, value, select_attrs, renderer))

        return format_html(
            '<div data-controller="w-rules" '
            'data-action="change@window->w-rules#resolve">{}</div>',
            mark_safe("".join(selects)),  # noqa: S308
        )


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
    container_design = StreamField(
        [("design", SpacedDesignBlock())],
        blank=True,
        max_num=1,
        use_json_field=True,
        verbose_name=_("Container design"),
        help_text=_("Styling for the wrapper around this field."),
    )
    upload_design = StreamField(
        [("design", UploadWidgetDesignBlock())],
        blank=True,
        max_num=1,
        use_json_field=True,
        verbose_name=_("Upload design"),
    )
    choice_options = StreamField(
        [("design", ChoiceOptionsDesignBlock())],
        blank=True,
        max_num=1,
        use_json_field=True,
        verbose_name=_("Choice options"),
    )

    panels = [
        MultiFieldPanel(
            [
                # field_type must be populated for previews to build the form field.
                # Set required_on_save=True on the field panel in case the model field
                # has been overridden.
                FieldPanel(
                    "field_type",
                    classname="formbuilder-type",
                    required_on_save=True,
                ),
                FieldPanel("required"),
                FieldPanel(
                    "model_field",
                    widget=ModelFieldSelect(empty_label=_("Use the field name")),
                ),
                FieldPanel("label"),
                FieldPanel("help_text"),
                PrefixedRulesPanel(
                    "choices",
                    classname="formbuilder-choices",
                    match="any",
                    rules={
                        "field_type": CHOICE_FIELD_TYPES,
                    },
                ),
                PrefixedRulesPanel(
                    "default_value",
                    classname="formbuilder-default",
                    match="any",
                    rules={
                        "field_type": DEFAULT_VALUE_FIELD_TYPES,
                    },
                ),
                FieldRowPanel(
                    [
                        FieldPanel("input_design"),
                        FieldPanel("label_design"),
                    ],
                    heading=_("Design"),
                    classname="collapsed",
                ),
                FieldRowPanel(
                    [
                        FieldPanel("container_design"),
                        PrefixedRulesPanel(
                            "choice_options",
                            rules={"field_type": CHOICE_OPTIONS_FIELD_TYPES},
                        ),
                    ],
                    heading=_("Container and choices"),
                    classname="collapsed",
                ),
                PrefixedRulesPanel(
                    "upload_design",
                    rules={"field_type": get_upload_field_type_keys},
                ),
            ],
            attrs={
                "data-controller": "w-rules",
                "data-action": "change->w-rules#resolve",
            },
        ),
    ]

    class Meta(AbstractFormField.Meta):
        abstract = True

    @property
    def is_upload(self):
        """Whether this field accepts a file upload."""
        return is_upload_field_type(self.field_type)

    def get_input_css(self) -> str:
        return build_design_css(
            self.input_design[0].value if self.input_design else None
        )

    def get_label_css(self) -> str:
        return build_design_css(
            self.label_design[0].value if self.label_design else None
        )

    def get_container_css(self) -> str:
        return build_design_css(
            self.container_design[0].value if self.container_design else None
        )

    def get_container_style(self) -> str:
        return build_background_style(
            self.container_design[0].value if self.container_design else None
        )

    def get_choice_options_css(self) -> str:
        value = self.choice_options[0].value if self.choice_options else None
        return build_class(
            build_design_css(value),
            build_design_css((value or {}).get("layout_design")),
        )

    def get_choice_options_style(self) -> str:
        return build_background_style(
            self.choice_options[0].value if self.choice_options else None
        )

    def get_widget_design(self):
        value = self.upload_design[0].value if self.upload_design else None
        value = value or {}
        return {
            "tray_css": build_design_css(value.get("tray")),
            "item_css": build_design_css(value.get("item")),
            "render": value.get("render") or "thumbnail",
            "fallback": value.get("fallback") or "icon",
        }
