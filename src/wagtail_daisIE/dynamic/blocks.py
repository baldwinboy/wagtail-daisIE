"""Blocks for binding configured context models to a page or menu."""

from __future__ import annotations

import json
import re

from django import forms
from django.core.exceptions import ValidationError
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks.compact import DaisieStructBlock
from ..choicelist import ChoiceList
from .registry import (
    get_context_model,
    get_context_model_choices,
    get_context_models,
    get_context_models_state,
)


BINDING_MODE_CHOICES = ChoiceList(
    [
        ("automatic", _("Automatic")),
        ("url", _("From the URL")),
        ("fixed", _("Specific instance")),
    ],
    "BINDING_MODE_CHOICES",
)
BINDING_LOOKUP_IN_CHOICES = ChoiceList(
    [
        ("path", _("Path parameter")),
        ("query", _("Query parameter")),
    ],
    "BINDING_LOOKUP_IN_CHOICES",
)


class HiddenValueBlock(blocks.FieldBlock):
    """Store a value in a hidden input; the value is chosen in the form template."""

    def __init__(self, required=False, **kwargs):
        self.field = forms.CharField(
            required=required,
            widget=forms.HiddenInput(
                attrs={
                    "data-controller": "w-sync",
                    "data-action": ("change->w-sync#apply load@window->w-sync#apply"),
                    "data-w-sync-target-value": '[data-current-for="__NAME__"]',
                    "data-w-sync-debounce-value": "0",
                }
            ),
        )
        super().__init__(**kwargs)

    class Meta:
        icon = "snippet"


class ContextBindingBlock(DaisieStructBlock):
    """Expose a context value, resolved automatically, from the URL, or pinned."""

    key = blocks.ChoiceBlock(
        choices=get_context_model_choices,
        label=_("Value"),
        help_text=_("The variable content can reference, e.g. {{ meeting }}."),
    )
    mode = blocks.ChoiceBlock(
        choices=BINDING_MODE_CHOICES,
        default="automatic",
        required=False,
        label=_("Source"),
    )
    object_id = HiddenValueBlock(required=False, label=_("Instance"))
    lookup_field = blocks.CharBlock(
        required=False,
        blank=True,
        label=_("Parameter name"),
        help_text=_("The URL parameter to look up (defaults to the model config)."),
    )
    lookup_in = blocks.ChoiceBlock(
        choices=BINDING_LOOKUP_IN_CHOICES,
        default="path",
        required=False,
        label=_("Read from"),
        help_text=_("Where in the request URL the value is read from."),
    )
    lookup_pattern = blocks.CharBlock(
        required=False,
        blank=True,
        max_length=200,
        label=_("Value pattern"),
        help_text=_(
            "Optional regular expression the value must fully match, e.g. [\\w-]+."
        ),
    )
    fallback = blocks.CharBlock(
        max_length=255,
        required=False,
        blank=True,
        help_text=_(
            "Shown when the value cannot be resolved (e.g. no signed-in user)."
        ),
    )

    def get_form_context(self, value, prefix="", errors=None):
        context = super().get_form_context(value, prefix=prefix, errors=errors)
        context["context_models"] = get_context_models_state()
        multi_mode_keys = [
            key for key, config in get_context_models().items() if len(config.modes) > 1
        ]
        context["multi_mode_json"] = json.dumps(multi_mode_keys)
        try:
            context["binding_results_url"] = reverse("wagtail_daisIE:binding_results")
        except NoReverseMatch:  # pragma: no cover - admin not mounted
            context["binding_results_url"] = ""
        return context

    @staticmethod
    def _object_exists(config, object_id):
        model = config.model
        if model is None:
            return False
        try:
            return model._default_manager.filter(pk=object_id).exists()
        except (TypeError, ValueError):
            return False

    def clean(self, value):
        value = super().clean(value)
        config = get_context_model(value.get("key"))
        if config is not None:
            modes = config.modes
            if value.get("mode") not in modes:
                value["mode"] = modes[0]
            if value.get("mode") == "fixed":
                object_id = value.get("object_id")
                if object_id and not self._object_exists(config, object_id):
                    value["object_id"] = ""
                if not value.get("object_id"):
                    raise ValidationError(
                        _("Choose an instance, or switch the source.")
                    )
        pattern = value.get("lookup_pattern") or ""
        if pattern:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValidationError(
                    _("Value pattern is not a valid regular expression: %(error)s")
                    % {"error": exc}
                ) from exc
        return value

    class Meta:
        icon = "group"
        label = _("Context binding")
        collapsed = True
        form_template = "wagtail_daisIE/admin/context_binding_form.html"
        form_attrs = {
            "data-controller": "w-rules",
            "data-action": "change->w-rules#resolve",
        }
        form_layout = blocks.BlockGroup(
            children=[
                "key",
                "fallback",
                "mode",
                "object_id",
                "lookup_in",
                "lookup_field",
                "lookup_pattern",
            ],
            heading=_("Context binding"),
        )


CONTEXT_BINDING_BLOCKS = [
    ("binding", ContextBindingBlock()),
]
