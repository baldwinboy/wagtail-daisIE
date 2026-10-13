"""File-upload widgets with progressive client-side preview.

These render a native file input that still submits without JavaScript. The
attachments widget also renders edit-mode references as hidden inputs so they
survive an outside-the-input round trip; the ``file_input.js`` enhancement
clones the ``<template>`` to preview newly selected files.
"""

from __future__ import annotations

from django import forms

from .fields import MultipleFileInput


class AttachmentsFileInput(MultipleFileInput):
    """A multiple-file input that previews files and supports edit mode.

    Existing (edit-mode) references are rendered as hidden
    ``{name}-existing`` inputs and submitted alongside any new files; removing
    a card removes its hidden input, so it drops out of the value.
    """

    template_name = "wagtail_daisIE/forms/widgets/attachments_file_input.html"

    @staticmethod
    def _existing_values(value):
        if not value:
            return []
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value if item]
        return [str(value)]

    @staticmethod
    def _submitted_existing(data, name):
        key = f"{name}-existing"
        getter = getattr(data, "getlist", None)
        if getter is not None:
            values = getter(key)
        else:
            value = data.get(key)
            if value is None:
                return []
            values = value if isinstance(value, (list, tuple)) else [value]
        return [value for value in values if value]

    def value_from_datadict(self, data, files, name):
        new_files = super().value_from_datadict(data, files, name) or []
        return [*new_files, *self._submitted_existing(data, name)]

    def value_omitted_from_data(self, data, files, name):
        return super().value_omitted_from_data(data, files, name) and (
            f"{name}-existing" not in data
        )

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["existing"] = self._existing_values(value)
        context["widget"].update(self._design_context())
        return context

    def _design_context(self):
        design = getattr(self, "design", None) or {}
        return {
            "tray_css": design.get("tray_css", ""),
            "item_css": design.get("item_css", ""),
            "render": design.get("render", "thumbnail"),
            "fallback": design.get("fallback", "icon"),
        }

    @property
    def media(self):
        return forms.Media(js=["wagtail_daisIE/js/file_input.js"])


class ImageFileInput(forms.ClearableFileInput):
    """A single image picker that shows a click-to-change preview.

    Extends ``ClearableFileInput`` so the initial value renders and can be
    cleared when bound to a model image field; the template wraps the input in
    a clickable preview.
    """

    template_name = "wagtail_daisIE/forms/widgets/image_file_input.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        design = getattr(self, "design", None) or {}
        context["widget"].update(
            {
                "tray_css": design.get("tray_css", ""),
                "item_css": design.get("item_css", ""),
                "render": design.get("render", "thumbnail"),
                "fallback": design.get("fallback", "icon"),
            }
        )
        return context

    @property
    def media(self):
        return forms.Media(js=["wagtail_daisIE/js/file_input.js"])
