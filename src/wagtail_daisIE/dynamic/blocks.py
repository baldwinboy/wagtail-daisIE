"""Blocks for binding configured context models to a page or menu."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from .forms import DynamicInstanceField
from .registry import get_context_model, get_context_model_choices


class DynamicInstanceChooserBlock(blocks.FieldBlock):
    """Pick a specific instance of the binding's model."""

    def __init__(self, required=True, **kwargs):
        self.field = DynamicInstanceField(required=required)
        super().__init__(**kwargs)

    class Meta:
        icon = "snippet"


class ContextBindingBlock(blocks.StructBlock):
    """Expose a context value, resolved automatically, from the URL, or pinned."""

    key = blocks.ChoiceBlock(
        choices=get_context_model_choices,
        label=_("Value"),
        help_text=_("The variable content can reference, e.g. {{ meeting }}."),
    )
    mode = blocks.ChoiceBlock(
        choices=[
            ("automatic", _("Automatic")),
            ("url", _("From the URL")),
            ("fixed", _("Specific instance")),
        ],
        default="automatic",
        required=False,
        label=_("Source"),
    )
    object_id = DynamicInstanceChooserBlock(required=False, label=_("Instance"))
    lookup_field = blocks.CharBlock(
        required=False,
        blank=True,
        label=_("Parameter name"),
        help_text=_("The URL parameter to look up (defaults to the model config)."),
    )
    lookup_in = blocks.ChoiceBlock(
        choices=[
            ("path", _("Path parameter")),
            ("query", _("Query parameter")),
        ],
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
        label=_("Fallback"),
        help_text=_(
            "Shown when the value cannot be resolved (e.g. no signed-in user)."
        ),
    )

    def clean(self, value):
        value = super().clean(value)
        config = get_context_model(value.get("key"))
        if config is not None:
            modes = config.modes
            if value.get("mode") not in modes:
                value["mode"] = modes[0]
            if value.get("mode") == "fixed" and not value.get("object_id"):
                raise ValidationError(_("Choose an instance, or switch the source."))
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
        form_layout = blocks.BlockGroup(
            children=[
                "key",
                "mode",
                "object_id",
                "lookup_in",
                "lookup_field",
                "lookup_pattern",
                "fallback",
            ],
            heading=_("Context binding"),
        )


CONTEXT_BINDING_BLOCKS = [
    ("binding", ContextBindingBlock()),
]
