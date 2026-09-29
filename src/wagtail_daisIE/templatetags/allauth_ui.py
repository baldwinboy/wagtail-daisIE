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
        return "file-input w-full validator"
    if isinstance(widget, Textarea):
        return "textarea w-full validator"
    if isinstance(widget, (Select, SelectMultiple)):
        return "select w-full validator"
    return "input w-full validator"


def _label_markup(field, unlabeled, extra_class=""):
    if unlabeled or not field.label:
        return ""
    required = ""
    if field.field.required:
        required = ' <span class="text-error" aria-hidden="true">*</span>'
    classes = "label" + (f" {extra_class}" if extra_class else "")
    return format_html(
        '<label class="{}" for="{}">{}{}</label>',
        classes,
        field.id_for_label,
        field.label,
        mark_safe(required),  # noqa: S308
    )


def _is_otp(field, presentation):
    if presentation == "otp":
        return True
    return field.field.widget.attrs.get("autocomplete") == "one-time-code"


def _otp_markup(field, attrs, size="", color="", joined=False):
    """Render a one-time-code field with the daisyUI ``otp`` component."""
    widget = field.field.widget
    raw_maxlength = widget.attrs.get("maxlength") or 6
    try:
        count = int(raw_maxlength)
    except (TypeError, ValueError):
        count = 6
    otp_attrs = {
        "inputmode": "numeric",
        "autocomplete": "one-time-code",
        "maxlength": count,
        "pattern": f"[0-9]{{{count}}}",
    }
    for key in ("form", "aria-invalid", "aria-describedby"):
        if key in attrs:
            otp_attrs[key] = attrs[key]
    widget_html = field.as_widget(attrs=otp_attrs)
    classes = "otp"
    if joined:
        classes += " otp-joined"
    if size:
        classes += f" otp-{size}"
    if color:
        classes += f" otp-{color}"
    spans = mark_safe("".join("<span></span>" for _ in range(count)))  # noqa: S308
    return format_html('<label class="{}">{} {}</label>', classes, spans, widget_html)


def _field_extras(body, field, errors):
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
def daisie_form_field(
    field,
    unlabeled=False,
    input_class="",
    label_class="",
    form_id="",
    presentation="",
    otp_size="",
    otp_color="",
    otp_joined=False,
):
    """Render a bound form field with DaisyUI markup and accessibility wiring."""
    widget = field.field.widget
    css = _widget_classes(widget)
    if input_class:
        css = f"{css} {input_class}".strip()
    errors = [str(error) for error in field.errors]

    attrs = {"class": css}
    if form_id:
        attrs["form"] = form_id
    described_by = []
    if errors:
        attrs["aria-invalid"] = "true"
        if field.id_for_label:
            described_by.append(f"{field.id_for_label}-error")
    if field.help_text and field.id_for_label:
        described_by.append(f"{field.id_for_label}-help")
    if described_by:
        attrs["aria-describedby"] = " ".join(described_by)

    if _is_otp(field, presentation):
        body = _otp_markup(
            field, attrs, size=otp_size, color=otp_color, joined=otp_joined
        )
        return _field_extras(body, field, errors)

    widget_html = field.as_widget(attrs=attrs)
    label_html = _label_markup(field, unlabeled, extra_class=label_class)

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


@register.simple_tag(takes_context=True)
def daisie_auth_theme(context):
    """Return the theme allauth layouts should render with.

    Prefers any ``daisyui_theme`` already resolved into the context (including
    an active ``AllauthPageOverride`` theme), then falls back to the default.
    """
    theme = context.get("daisyui_theme")
    if theme is not None:
        return theme
    from ..models import DaisyUITheme

    try:
        return DaisyUITheme.objects.filter(default=True).first()
    except Exception:  # pragma: no cover - table may not exist
        return None


@register.inclusion_tag("wagtail_daisIE/allauth/page_body.html", takes_context=True)
def daisie_allauth_page(context, override=None, form=None):
    """Render an ``AllauthPageOverride`` body (or nothing when inactive).

    The body is rendered with the form, the body stream (for ``auth_form`` to
    find placed fields) and the page-design channels in context, so content
    blocks and ``auth_field`` blocks behave like a normal page.
    """
    request = context.get("request")
    if override is None:
        override = context.get("daisie_allauth_override")
    if form is None:
        form = context.get("form")
    if override is None:
        return {"override": None}
    from ..allauth_ui.blocks import ALLAUTH_FORM_ID

    data = {
        "override": override,
        "form": form,
        "request": request,
        "form_id": ALLAUTH_FORM_ID,
        "body": override.body,
        "page_background_css": override.get_background_css(),
    }
    data.update(override.get_page_design_css())
    return data
