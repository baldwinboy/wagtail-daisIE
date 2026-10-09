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

from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks import InlineMarkupBlock
from ..base_blocks.compact import DaisieStreamBlock, DaisieStructBlock
from ..blocks.inputs import FIELD_BLOCKS
from ..blocks.link import ButtonBlock
from ..choicelist import ChoiceList
from ..choices.feedback import (
    ALERT_COLOR_CHOICES,
    ALERT_DIRECTION_CHOICES,
    ALERT_STYLE_CHOICES,
)
from ..icons.blocks import IconChooserBlock
from .actions import get_action_choices


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
            children=["text", "icon", "color", "style", "direction"],
            heading=_("Confirmation alert"),
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

    class Meta:
        icon = "link"
        label = _("Button")
        collapsed = True
        template = "wagtail_daisIE/blocks/data/action_button_inner.html"
        form_layout = blocks.BlockGroup(
            children=["text", "icon", "icon_after", "make_parent_clickable"],
            settings=["design", "audience"],
        )


class ActionBlock(DaisieStructBlock):
    """A themed action button plus its optional confirmation alert."""

    action = blocks.ChoiceBlock(choices=get_action_choices)
    target_expression = blocks.CharBlock(
        required=False,
        blank=True,
        help_text=_("Sent as 'target', e.g. {{ bread.pk }}."),
    )
    button = ActionButtonBlock()
    confirmation = ActionConfirmationBlock(
        required=False,
        help_text=_("Optional alert shown after the action runs."),
    )

    class Meta:
        icon = "plus"
        label = _("Action")
        group = _("Data")
        collapsed = True
        template = "wagtail_daisIE/blocks/data/action_button.html"
        form_layout = blocks.BlockGroup(
            children=["action", "target_expression", "button", "confirmation"],
            settings=[],
        )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
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


class ActionFormBlock(DaisieStructBlock):
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
    fields = DaisieStreamBlock(FIELD_BLOCKS, label=_("Fields"))
    button = ActionButtonBlock()
    confirmation = ActionConfirmationBlock(
        required=False,
        help_text=_("Optional alert shown after the action runs."),
    )
    behaviour = blocks.ChoiceBlock(
        choices=ACTION_FORM_BEHAVIOUR_CHOICES,
        default="inline",
        label=_("After submit"),
        help_text=_("How the browser responds when the action succeeds."),
    )

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
            settings=[],
        )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        value = value or {}
        action_key = value.get("action", "")
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
    confirmation = confirmation or {}
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
