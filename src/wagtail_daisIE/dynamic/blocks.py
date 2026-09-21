"""Blocks for binding configured context models to a page or menu."""

from __future__ import annotations

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
        label=_("URL keyword"),
        help_text=_("The URL keyword to look up (defaults to the model config)."),
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
        return value

    class Meta:
        icon = "group"
        label = _("Context binding")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=["key", "mode", "object_id", "lookup_field", "fallback"],
            heading=_("Context binding"),
        )


CONTEXT_BINDING_BLOCKS = [
    ("binding", ContextBindingBlock()),
]
