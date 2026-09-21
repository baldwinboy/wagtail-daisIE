"""Template tags powering the DaisyUI allauth UI."""

from __future__ import annotations

from django import template
from django.forms import (
    CheckboxInput,
    CheckboxSelectMultiple,
    ClearableFileInput,
    FileInput,
    RadioSelect,
    Select,
    SelectMultiple,
    Textarea,
)
from django.utils.html import format_html
from django.utils.safestring import mark_safe


register = template.Library()


def _widget_classes(widget):
    if isinstance(widget, (CheckboxInput, CheckboxSelectMultiple)):
        return "checkbox"
    if isinstance(widget, RadioSelect):
        return "radio"
    if isinstance(widget, (FileInput, ClearableFileInput)):
        return "file-input w-full"
    if isinstance(widget, Textarea):
        return "textarea w-full"
    if isinstance(widget, (Select, SelectMultiple)):
        return "select w-full"
    return "input w-full"


def _label_markup(field, unlabeled):
    if unlabeled or not field.label:
        return ""
    required = ""
    if field.field.required:
        required = ' <span class="text-error" aria-hidden="true">*</span>'
    return format_html(
        '<label class="label" for="{}">{}{}</label>',
        field.id_for_label,
        field.label,
        mark_safe(required),  # noqa: S308
    )


@register.simple_tag
def daisie_form_field(field, unlabeled=False):
    """Render a bound form field with DaisyUI markup and accessibility wiring."""
    widget = field.field.widget
    css = _widget_classes(widget)
    errors = [str(error) for error in field.errors]

    attrs = {"class": css}
    described_by = []
    if errors:
        attrs["aria-invalid"] = "true"
        if field.id_for_label:
            described_by.append(f"{field.id_for_label}-error")
    if field.help_text and field.id_for_label:
        described_by.append(f"{field.id_for_label}-help")
    if described_by:
        attrs["aria-describedby"] = " ".join(described_by)

    widget_html = field.as_widget(attrs=attrs)
    label_html = _label_markup(field, unlabeled)

    if isinstance(widget, CheckboxInput):
        body = format_html(
            '<label class="label cursor-pointer justify-start gap-3">'
            '{}<span class="label-text">{}</span></label>',
            widget_html,
            field.label,
        )
    elif isinstance(widget, (RadioSelect, CheckboxSelectMultiple)):
        body = format_html(
            '<fieldset class="fieldset w-full">'
            '<legend class="fieldset-legend">{}</legend>{}</fieldset>',
            field.label,
            widget_html,
        )
    else:
        body = format_html("{}{}", label_html, widget_html)

    help_html = ""
    if field.help_text:
        help_html = format_html(
            '<p class="label" id="{}-help">{}</p>',
            field.id_for_label,
            field.help_text,
        )

    error_html = ""
    if errors:
        error_html = format_html(
            '<p class="label text-error" id="{}-error" role="alert">{}</p>',
            field.id_for_label,
            " ".join(errors),
        )

    return mark_safe(body + help_html + error_html)  # noqa: S308


@register.simple_tag
def daisie_auth_theme():
    """Return the default :class:`DaisyUITheme` for allauth layouts, if any."""
    from ..models import DaisyUITheme

    try:
        return DaisyUITheme.objects.filter(default=True).first()
    except Exception:  # pragma: no cover - table may not exist
        return None
