"""Abstract form field with per-field design and model-field linking."""

from __future__ import annotations

from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.forms.models import AbstractFormField
from wagtail.fields import StreamField

from ..base_blocks.css import build_design_css
from ..base_blocks.design import TypographyDesignBlock


class ModelFieldSelect(forms.Select):
    """A select populated client-side from the page's bound model."""

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


class DaisieFormField(AbstractFormField):
    """A Wagtail form field that can be styled and linked to a model field."""

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
        [("design", TypographyDesignBlock())],
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
            widget=ModelFieldSelect(attrs={"data-daisie-model-field": ""}),
        ),
        FieldPanel("input_design"),
        FieldPanel("label_design"),
    ]

    class Meta(AbstractFormField.Meta):
        abstract = True

    def get_input_css(self):
        return build_design_css(
            self.input_design[0].value if self.input_design else None
        )

    def get_label_css(self):
        return build_design_css(
            self.label_design[0].value if self.label_design else None
        )
