"""DaisyUI-styled form builder for Wagtail form pages.

Adds DaisyUI classes to widgets and applies each field's per-field design.
"""

from __future__ import annotations

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from wagtail.contrib.forms.forms import FormBuilder

from .registry import get_form_field_type


class DaisyUIFormBuilder(FormBuilder):
    """Adds DaisyUI classes and per-field design to Wagtail form fields."""

    def _styled(self, options, widget, css_class, attrs=None):
        if isinstance(widget, type):
            widget = widget()
        if attrs:
            widget.attrs.update(attrs)
        existing = widget.attrs.get("class", "")
        widget.attrs["class"] = f"{existing} {css_class}".strip()
        options["widget"] = widget
        return options

    @staticmethod
    def _apply_widget_attrs(widget, css_class, attrs):
        if attrs:
            widget.attrs.update(attrs)
        if css_class:
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css_class}".strip()

    def get_create_field_function(self, field_type):
        """Return the builder for a field type.

        Types registered in ``WAGTAIL_DAISIE_FORM_FIELD_TYPES`` are built from
        their configuration; everything else falls back to Wagtail's default
        ``create_<type>_field`` dispatch.
        """
        spec = get_form_field_type(field_type)
        if spec is None:
            return super().get_create_field_function(field_type)

        def create_field(field, options):
            options = dict(options)
            options.update(spec.options)
            if spec.widget is not None:
                self._styled(options, spec.widget, spec.css, spec.widget_attrs)
            builder = spec.field
            if builder is None:
                raise ImproperlyConfigured(
                    _(
                        "The %(type)r form field type is missing a 'field' entry "
                        "in WAGTAIL_DAISIE_FORM_FIELD_TYPES."
                    )
                    % {"type": spec.key}
                )
            if isinstance(builder, type):
                django_field = builder(**options)
            else:
                django_field = builder(field, options)
            if spec.widget is None and (spec.css or spec.widget_attrs):
                self._apply_widget_attrs(
                    django_field.widget, spec.css, spec.widget_attrs
                )
            return self._design(field, django_field)

        return create_field

    def _design(self, form_field, django_field):
        input_css = ""
        label_css = ""
        get_input = getattr(form_field, "get_input_css", None)
        if callable(get_input):
            input_css = get_input() or ""
        get_label = getattr(form_field, "get_label_css", None)
        if callable(get_label):
            label_css = get_label() or ""
        if input_css:
            widget = django_field.widget
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {input_css}".strip()
        django_field.input_css = input_css
        django_field.label_css = label_css
        return django_field

    def create_singleline_field(self, field, options):
        self._styled(options, forms.TextInput, "input w-full")
        return self._design(field, super().create_singleline_field(field, options))

    def create_multiline_field(self, field, options):
        self._styled(options, forms.Textarea, "textarea w-full")
        return self._design(field, super().create_multiline_field(field, options))

    def create_date_field(self, field, options):
        self._styled(options, forms.DateInput(attrs={"type": "date"}), "input w-full")
        return self._design(field, super().create_date_field(field, options))

    def create_datetime_field(self, field, options):
        self._styled(
            options,
            forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "input w-full",
        )
        return self._design(field, super().create_datetime_field(field, options))

    def create_email_field(self, field, options):
        self._styled(options, forms.EmailInput, "input w-full")
        return self._design(field, super().create_email_field(field, options))

    def create_url_field(self, field, options):
        self._styled(options, forms.URLInput, "input w-full")
        return self._design(field, super().create_url_field(field, options))

    def create_number_field(self, field, options):
        self._styled(options, forms.NumberInput, "input w-full")
        return self._design(field, super().create_number_field(field, options))

    def create_dropdown_field(self, field, options):
        self._styled(options, forms.Select, "select w-full")
        return self._design(field, super().create_dropdown_field(field, options))

    def create_multiselect_field(self, field, options):
        self._styled(options, forms.SelectMultiple, "select w-full")
        return self._design(field, super().create_multiselect_field(field, options))

    def create_radio_field(self, field, options):
        self._styled(options, forms.RadioSelect, "radio")
        return self._design(field, super().create_radio_field(field, options))

    def create_checkboxes_field(self, field, options):
        self._styled(options, forms.CheckboxSelectMultiple, "checkbox")
        return self._design(field, super().create_checkboxes_field(field, options))

    def create_checkbox_field(self, field, options):
        self._styled(options, forms.CheckboxInput, "checkbox")
        return self._design(field, super().create_checkbox_field(field, options))

    def create_hidden_field(self, field, options):
        return super().create_hidden_field(field, options)
