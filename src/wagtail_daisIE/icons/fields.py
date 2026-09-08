from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from .widgets import IconChooserWidget


class IconField(models.CharField):
    """A universal icon value stored as ``"<prefix>:<name>"``.

    Legacy raw CSS class strings (e.g. ``"fa-solid fa-home"``) are also
    accepted and rendered as ``<i class="...">``.
    """

    description = _("A universal icon value (prefix:name)")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 255)
        kwargs.setdefault("blank", True)
        kwargs.setdefault("default", "")
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {"widget": IconChooserWidget()}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class IconBlockField(forms.CharField):
    """Form field used by :class:`~wagtail_daisIE.icons.blocks.IconChooserBlock`."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 255)
        kwargs.setdefault("widget", IconChooserWidget())
        super().__init__(*args, **kwargs)
