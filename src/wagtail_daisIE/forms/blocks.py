"""Page-body blocks that can place a bound form field inline."""

from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..blocks.content import ALL_CONTENT_BLOCKS, ContentBlock


#: ``StreamChild.block_type`` used by :class:`FormFieldBlock`.
FORM_FIELD_BLOCK_TYPE = "form_field"


class FormFieldSelect(forms.Select):
    """A select populated client-side from the page's bound form fields."""

    def optgroups(self, name, value, attrs=None):
        groups = super().optgroups(name, value, attrs)
        if any(options for _index, options, _subindex in groups):
            return groups
        selected = [item for item in value if item not in (None, "")]
        if not selected:
            return groups
        return [
            (
                None,
                [
                    self.create_option(name, item, item, True, index)
                    for index, item in enumerate(selected)
                ],
                0,
            )
        ]


class FormFieldBlock(blocks.FieldBlock):
    """Render one of the page's bound form fields at this point in the body.

    The stored value is the ``clean_name`` of a
    :class:`wagtail_daisIE.forms.fields.DaisieFormField`. At render time the
    matching bound field is looked up on the page's form and rendered with the
    same markup as the standard field loop, so its input, label, help text and
    errors all behave as normal. The input is associated with the page form via
    the HTML ``form`` attribute rather than by nesting the body in a ``<form>``,
    which keeps blocks that render their own form valid.
    """

    def __init__(self, required=True, **kwargs):
        self.field = forms.CharField(
            required=required,
            max_length=255,
            widget=FormFieldSelect(attrs={"data-daisie-form-field": ""}),
        )
        super().__init__(**kwargs)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        form = (parent_context or {}).get("form")
        name = value or ""
        context["bound_field"] = (
            form[name] if form is not None and name in form.fields else None
        )
        return context

    class Meta:
        icon = "form"
        label = _("Form field")
        template = "wagtail_daisIE/forms/form_field_block.html"


class FormContentBlock(ContentBlock):
    """A page body that also allows placing the page's own form fields."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "local_blocks",
            [*ALL_CONTENT_BLOCKS, (FORM_FIELD_BLOCK_TYPE, FormFieldBlock())],
        )
        super().__init__(*args, **kwargs)


def placed_field_names(body):
    """Return the clean names of ``form_field`` blocks in ``body``, in order."""
    if not body:
        return []
    return [
        child.value
        for child in body
        if child.block_type == FORM_FIELD_BLOCK_TYPE and child.value
    ]


def duplicate_field_names(body):
    """Return clean names placed more than once in ``body``, unique and ordered."""
    seen = set()
    duplicates = []
    for name in placed_field_names(body):
        if name in seen and name not in duplicates:
            duplicates.append(name)
        seen.add(name)
    return duplicates


__all__ = [
    "duplicate_field_names",
    "FORM_FIELD_BLOCK_TYPE",
    "FormContentBlock",
    "FormFieldBlock",
    "FormFieldSelect",
    "placed_field_names",
]
