"""DaisyUI-styled form builder for Wagtail form pages.

Adds DaisyUI classes to widgets and applies each field's per-field design.
"""

from __future__ import annotations

from django import forms
from wagtail.contrib.forms.forms import FormBuilder


class DaisyUIFormBuilder(FormBuilder):
    """Adds DaisyUI classes and per-field design to Wagtail form fields."""

    def _styled(self, options, widget, css_class):
        if isinstance(widget, type):
            widget = widget()
        existing = widget.attrs.get("class", "")
        widget.attrs["class"] = f"{existing} {css_class}".strip()
        options["widget"] = widget
        return options

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
