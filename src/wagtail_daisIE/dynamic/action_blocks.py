"""Action blocks: a themed button wired to a developer-defined action.

An action is a small form that POSTs to a configured handler (see
``wagtail_daisIE.dynamic.actions``). The block is a struct of:

* the action identity (``action`` + ``target_expression``),
* a themed **button** (a subclass of the normal button block, so it inherits
  the same appearance/design logic), and
* an optional **confirmation** alert whose text/icon/colour are added to the
  Django messages framework when the action runs. Messages survive the POST
  redirect and are rendered as DaisyUI ``alert`` components by
  ``{% daisie_messages %}``.

The button can also be configured to make its parent card clickable, in which
case the button itself renders nothing and the card (see ``blocks/cards.py``)
renders the trigger.
"""

from __future__ import annotations

import logging

from django.core.exceptions import ValidationError
from django.urls import NoReverseMatch, reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks import (
    ButtonAppearanceBlock,
    InlineMarkupBlock,
    SpacedDesignBlock,
    collapsed_group,
)
from ..base_blocks.compact import DaisieStreamBlock, DaisieStructBlock
from ..base_blocks.css import (
    build_background_style,
    build_design_css,
    build_layout_item_css,
)
from ..base_blocks.layout_design import LayoutBlock, LayoutItemDesignBlock
from ..base_blocks.utils import build_class
from ..base_blocks.visibility import VisibilityBlock, VisibilityMixin
from ..blocks.inputs import AUTOCOMPLETE_BLOCKS, FIELD_BLOCKS
from ..blocks.link import ButtonBlock
from ..choicelist import ChoiceList
from ..choices.feedback import (
    ALERT_COLOR_CHOICES,
    ALERT_DIRECTION_CHOICES,
    ALERT_STYLE_CHOICES,
)
from ..icons.blocks import IconChooserBlock
from .actions import (
    ACTION_FIELD_COMMON_KEYS,
    ACTION_FIELD_TYPES,
    get_action_choices,
    get_action_fields,
)


logger = logging.getLogger(__name__)


ACTION_FORM_BEHAVIOUR_CHOICES = ChoiceList(
    [
        ("inline", _("Update in place")),
        ("reload", _("Reload the page")),
        ("navigate", _("Follow the response")),
    ],
    "ACTION_FORM_BEHAVIOUR_CHOICES",
)


#: Alert classes a visitor is allowed to submit with a confirmation message.
ALERT_TAGS = frozenset(
    choice
    for choice in (
        *(value for value, _label in ALERT_COLOR_CHOICES),
        *(value for value, _label in ALERT_STYLE_CHOICES),
        *(value for value, _label in ALERT_DIRECTION_CHOICES),
    )
    if choice
)

#: Alert colour -> Django messages level.
ALERT_LEVELS = {
    "alert-success": "success",
    "alert-warning": "warning",
    "alert-error": "error",
    "alert-info": "info",
}


#: Legacy confirmation struct fields that make the confirmation meaningful.
_CONFIRMATION_VALUE_KEYS = (
    "title",
    "text",
    "confirm_label",
    "icon",
    "color",
    "style",
    "direction",
)


_BUTTON_STATE_KEYS = ("color", "style", "size", "behavior", "modifier")


def _appearance_css(value, fallback):
    """Return button appearance classes, or ``fallback`` when unconfigured."""
    if not value:
        return fallback
    for state in ("normal", "hover", "active"):
        state_value = value.get(state) or {}
        if any(state_value.get(key) for key in _BUTTON_STATE_KEYS):
            return build_design_css({"button_appearance": value}) or fallback
    return fallback


def _preset_field_value(spec):
    """Convert an action config field spec into an input block value."""
    field_type = spec.get("type")
    allowed = ACTION_FIELD_COMMON_KEYS | ACTION_FIELD_TYPES.get(field_type, frozenset())
    value = {key: spec[key] for key in allowed if key != "type" and key in spec}
    if isinstance(value.get("options"), (list, tuple)):
        value["options"] = "\n".join(str(option) for option in value["options"])
    if isinstance(value.get("selected"), (list, tuple)):
        value["selected"] = ", ".join(str(item) for item in value["selected"])
    return value


def _stable_field_id(parent_context, action_key, index, name):
    """Build a stable, unique id for a configured preset field."""
    form = (parent_context or {}).get("block")
    form_id = getattr(form, "id", "") or slugify(action_key) or "action"
    slug = slugify(name) or "field"
    return f"{form_id}-{index}-{slug}"


def _legacy_stream_value(value):
    """Turn a non-empty legacy confirmation struct/dict into a stream list.

    Old StructBlock values serialise empty confirmation fields as a mapping of
    empty strings. Treat those as no confirmation so upgrades do not resurrect
    the empty dialog/alert this change removes.
    """
    if isinstance(value, dict):
        if any(value.get(key) for key in _CONFIRMATION_VALUE_KEYS):
            return [{"type": "item", "value": value}]
        return []
    return value


def _first_stream_item(value):
    """Return the first item value from a stream, dict, or ``None``."""
    if not value:
        return None
    if isinstance(value, dict):
        return value
    try:
        first = value[0]
    except (IndexError, KeyError, TypeError):
        return None
    first = getattr(first, "value", first)
    return first if hasattr(first, "get") else None


class ActionConfirmationBlock(DaisieStructBlock):
    """The confirmation alert added to Django messages when an action runs."""

    text = InlineMarkupBlock(
        max_length=255,
        label=_("Confirmation text"),
        help_text=_("Shown as a DaisyUI alert on the next page."),
    )
    icon = IconChooserBlock(required=False)
    color = blocks.ChoiceBlock(
        choices=ALERT_COLOR_CHOICES,
        default="",
        required=False,
        label=_("Colour"),
    )
    style = blocks.ChoiceBlock(
        choices=ALERT_STYLE_CHOICES,
        default="",
        required=False,
    )
    direction = blocks.ChoiceBlock(
        choices=ALERT_DIRECTION_CHOICES,
        default="",
        required=False,
    )

    class Meta:
        icon = "warning"
        label = _("Confirmation")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=[
                "text",
                collapsed_group(_("Icon"), "icon", icon="image"),
                "color",
                "style",
                "direction",
            ],
            heading=_("Confirmation alert"),
        )


class ActionConfirmationStreamBlock(DaisieStreamBlock):
    """One optional post-submit confirmation alert."""

    item = ActionConfirmationBlock()

    class Meta:
        icon = "warning"
        label = _("Confirmation alert")
        max_num = 1

    def to_python(self, value):
        return super().to_python(_legacy_stream_value(value))

    def bulk_to_python(self, values):
        return super().bulk_to_python(
            [_legacy_stream_value(value) or [] for value in values]
        )


class ActionConfirmBlock(DaisieStructBlock):
    """A pre-submit confirmation dialog for destructive actions."""

    title = InlineMarkupBlock(max_length=128, required=False, blank=True)
    text = InlineMarkupBlock(max_length=255, required=False, blank=True)
    confirm_label = blocks.CharBlock(
        max_length=64, required=False, blank=True, label=_("Confirm label")
    )
    panel_design = SpacedDesignBlock(
        required=False,
        label=_("Dialog panel design"),
    )
    confirm_appearance = ButtonAppearanceBlock(
        required=False,
        label=_("Confirm button"),
    )
    cancel_appearance = ButtonAppearanceBlock(
        required=False,
        label=_("Cancel button"),
    )

    class Meta:
        icon = "warning"
        label = _("Confirmation dialog")
        collapsed = True
        form_layout = blocks.BlockGroup(
            children=["title", "text", "confirm_label"],
            settings=[
                "panel_design",
                "confirm_appearance",
                "cancel_appearance",
            ],
            heading=_("Confirmation dialog"),
        )


class ActionConfirmStreamBlock(DaisieStreamBlock):
    """One optional pre-submit confirmation dialog."""

    item = ActionConfirmBlock()

    class Meta:
        icon = "warning"
        label = _("Confirmation dialog")
        max_num = 1

    def to_python(self, value):
        return super().to_python(_legacy_stream_value(value))

    def bulk_to_python(self, values):
        return super().bulk_to_python(
            [_legacy_stream_value(value) or [] for value in values]
        )


class ActionButtonBlock(ButtonBlock):
    """A normal button, restricted to the fields an action needs.

    It subclasses :class:`~wagtail_daisIE.blocks.link.ButtonBlock` so its
    appearance is built by exactly the same ``button_appearance`` logic as any
    other button; it only drops the link destination and renders a submit
    button instead of an anchor.
    """

    destination = None
    open_in_new_tab = None
    confirm = ActionConfirmStreamBlock(
        required=False,
        help_text=_("Show a confirmation dialog before the action is submitted."),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        confirm_value = _first_stream_item((value or {}).get("confirm")) or {}
        panel_design = confirm_value.get("panel_design")
        context["confirm"] = confirm_value
        context["has_confirm"] = bool(confirm_value)
        context["confirm_panel_css"] = build_design_css(panel_design)
        context["confirm_panel_style"] = build_background_style(panel_design)
        context["confirm_button_css"] = _appearance_css(
            confirm_value.get("confirm_appearance"), "btn btn-error"
        )
        context["cancel_button_css"] = _appearance_css(
            confirm_value.get("cancel_appearance"), "btn"
        )
        return context

    class Meta:
        icon = "link"
        label = _("Button")
        collapsed = True
        template = "wagtail_daisIE/blocks/data/action_button_inner.html"
        form_layout = blocks.BlockGroup(
            children=[
                "text",
                collapsed_group(_("Icon"), "icon", "icon_after", icon="image"),
                "label",
                "make_parent_clickable",
                "confirm",
            ],
            settings=["design", "audience"],
        )


class ActionBlock(VisibilityMixin, DaisieStructBlock):
    """A themed action button plus its optional confirmation alert."""

    action = blocks.ChoiceBlock(choices=get_action_choices)
    target_expression = blocks.CharBlock(
        required=False,
        blank=True,
        help_text=_("Sent as 'target', e.g. {{ bread.pk }}."),
    )
    button = ActionButtonBlock()
    confirmation = ActionConfirmationStreamBlock(
        required=False,
        help_text=_("Optional alert shown after the action runs."),
    )
    visibility = VisibilityBlock()

    class Meta:
        icon = "plus"
        label = _("Action")
        group = _("Data")
        collapsed = True
        template = "wagtail_daisIE/blocks/data/action_button.html"
        form_layout = blocks.BlockGroup(
            children=["action", "target_expression", "button", "confirmation"],
            settings=["visibility"],
        )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
        # The action form is a layout wrapper, not a design surface: do not let
        # an enclosing card/section style it. The nested button resolves its
        # own design (and menu item defaults) in ActionButtonBlock.get_context.
        context["block_css"] = ""
        context["block_style"] = ""
        action_key = value.get("action", "")
        try:
            context["action_url"] = reverse(
                "wagtail_daisIE_dynamic:action", args=[action_key]
            )
        except NoReverseMatch:
            context["action_url"] = ""

        # Forward the card marker so the nested button can stretch itself over
        # the card when ``make_parent_clickable`` is set (see blocks/link.py).
        context["card_clickable_container"] = bool(
            (parent_context or {}).get("card_clickable_container")
        )

        context.update(_confirmation_context(value.get("confirmation")))
        return context


class ActionFormBlock(VisibilityMixin, DaisieStructBlock):
    """A data-collecting form that POSTs its fields to a configured action.

    The fields are ordinary DaisyUI input blocks; the block renders one
    ``<form>`` containing them plus the themed submit button, so their values
    reach the action handler in ``request.POST``. On the front end the form is
    progressively enhanced with htmx (``hx-post``), but keeps a real
    ``action``/``method`` so it still works without JavaScript.
    """

    action = blocks.ChoiceBlock(choices=get_action_choices)
    target_expression = blocks.CharBlock(
        required=False,
        blank=True,
        help_text=_("Sent as 'target', e.g. {{ bread.pk }}."),
    )
    fields = DaisieStreamBlock(
        [*FIELD_BLOCKS, *AUTOCOMPLETE_BLOCKS],
        label=_("Fields"),
        required=False,
    )
    button = ActionButtonBlock()
    confirmation = ActionConfirmationStreamBlock(
        required=False,
        help_text=_("Optional alert shown after the action runs."),
    )
    behaviour = blocks.ChoiceBlock(
        choices=ACTION_FORM_BEHAVIOUR_CHOICES,
        default="inline",
        label=_("After submit"),
        help_text=_("How the browser responds when the action succeeds."),
    )
    container_design = SpacedDesignBlock(
        required=False,
        label=_("Form design"),
    )
    fields_layout = LayoutBlock(
        required=False,
        label=_("Field list layout"),
    )
    field_wrapper_layout = LayoutItemDesignBlock(
        required=False,
        label=_("Field wrapper layout"),
    )
    visibility = VisibilityBlock()

    class Meta:
        icon = "form"
        label = _("Action form")
        group = _("Data")
        collapsed = True
        template = "wagtail_daisIE/blocks/data/action_form.html"
        form_layout = blocks.BlockGroup(
            children=[
                "action",
                "target_expression",
                "fields",
                "button",
                "behaviour",
                "confirmation",
            ],
            settings=[
                "container_design",
                "fields_layout",
                "field_wrapper_layout",
                "visibility",
            ],
        )

    def _resolve_form_fields(self, value, action_key, parent_context):
        fields_block = self.child_blocks["fields"]
        editor_fields = list(value.get("fields") or [])
        specs = get_action_fields(action_key)

        def editor_entry(field, index):
            field_value = getattr(field, "value", field)
            name = str((field_value or {}).get("name") or "").strip()
            return {
                "type": getattr(field, "block_type", ""),
                "value": field_value,
                "id": getattr(field, "id", None)
                or _stable_field_id(parent_context, action_key, index, name),
            }

        if not specs:
            return fields_block.to_python(
                [
                    editor_entry(field, index)
                    for index, field in enumerate(editor_fields, start=1)
                ]
            )

        editor_by_name = {}
        for field in editor_fields:
            field_value = getattr(field, "value", field)
            name = str((field_value or {}).get("name") or "").strip()
            if name:
                editor_by_name.setdefault(name, field)

        config_names = {
            str(spec.get("name") or "").strip()
            for spec in specs
            if isinstance(spec, dict)
        }
        combined = []
        for index, spec in enumerate(specs, start=1):
            if not isinstance(spec, dict):
                continue
            name = str(spec.get("name") or "").strip()
            editor = editor_by_name.get(name)
            if editor is not None:
                combined.append(editor_entry(editor, index))
                continue

            field_type = spec.get("type")
            field_block = fields_block.child_blocks.get(field_type)
            if field_block is None:
                logger.warning("Skipping action field with unknown type %r", field_type)
                continue
            try:
                field_value = field_block.to_python(_preset_field_value(spec))
            except (TypeError, ValueError, ValidationError) as exc:
                logger.warning("Skipping invalid action field %r: %s", spec, exc)
                continue
            combined.append(
                {
                    "type": field_type,
                    "value": field_value,
                    "id": _stable_field_id(parent_context, action_key, index, name),
                }
            )

        next_index = len(specs) + 1
        for field in editor_fields:
            field_value = getattr(field, "value", field)
            name = str((field_value or {}).get("name") or "").strip()
            if name and name in config_names:
                continue
            combined.append(editor_entry(field, next_index))
            next_index += 1
        return fields_block.to_python(combined)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
        design = value.get("container_design")
        # The form design styles the <form> only. Do not write it into
        # ``container_css``: fields keep the page channel and their own design.
        context["form_css"] = build_design_css(design)
        context["form_style"] = build_background_style(design)

        layout_value = value.get("fields_layout") or {}
        layout_choice = layout_value.get("layout")
        context["fields_css"] = build_class(
            "w-full" if layout_choice else "flex w-full flex-col",
            build_design_css(layout_value),
        )
        item_value = value.get("field_wrapper_layout") or {}
        item_css = build_layout_item_css(item_value, grid=layout_choice == "grid")
        item_size_keys = ["width", "basis", "grow"]
        if layout_choice == "grid":
            item_size_keys.extend(["grid_column_span", "grid_row_span"])
        context["field_wrapper_css"] = build_class(
            "" if any(item_value.get(key) for key in item_size_keys) else "w-full",
            item_css,
        )

        action_key = value.get("action", "")
        context["form_fields"] = self._resolve_form_fields(
            value, action_key, parent_context
        )
        try:
            context["action_url"] = reverse(
                "wagtail_daisIE_dynamic:action", args=[action_key]
            )
        except NoReverseMatch:
            context["action_url"] = ""
        context.update(_confirmation_context(value.get("confirmation")))
        return context


def _confirmation_context(confirmation):
    """Message text/tags/level shared by the action block forms."""
    confirmation = _first_stream_item(confirmation) or {}
    tags = [
        str(token)
        for token in (
            confirmation.get("color"),
            confirmation.get("style"),
            confirmation.get("direction"),
        )
        if token
    ]
    return {
        "has_confirmation": bool(confirmation),
        "message_text": str(confirmation.get("text") or ""),
        "message_icon": str(confirmation.get("icon") or ""),
        "message_tags": " ".join(tags),
        "message_level": ALERT_LEVELS.get(str(confirmation.get("color") or ""), "info"),
    }


#: Options for developer-facing docs / introspection.
__all__ = [
    "ACTION_FORM_BEHAVIOUR_CHOICES",
    "ActionBlock",
    "ActionButtonBlock",
    "ActionConfirmationBlock",
    "ActionFormBlock",
    "ALERT_LEVELS",
    "ALERT_TAGS",
]
