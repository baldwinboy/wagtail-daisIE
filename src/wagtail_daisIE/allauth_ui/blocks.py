"""DaisyUI blocks for designing allauth account pages.

An :class:`~wagtail_daisIE.allauth_ui.models.AllauthPageOverride` body is a
normal page body (every content block) plus two allauth-specific blocks:

* ``auth_form`` — renders the real allauth ``<form>`` (CSRF, hidden fields and
  any fields the author did not place explicitly).
* ``auth_field`` — renders one of the view's fields at this point in the body,
  associated with the form via the HTML ``form`` attribute (exactly like the
  standard form page's ``form_field`` block).

Authors control the **look** only: which fields are shown and their validation
is always allauth's. Placing every field with ``auth_field`` also controls the
order; unplaced fields are appended by ``auth_form``.
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from ..base_blocks.css import build_design_css
from ..base_blocks.design import TypographyDesignBlock
from ..blocks.content import ALL_CONTENT_BLOCKS
from ..choicelist import ChoiceList
from ..choices import OTP_COLOR_CHOICES, OTP_SIZE_CHOICES
from .catalogue import get_all_account_field_choices


#: Fixed id used by ``auth_form`` and referenced by ``auth_field`` inputs via
#: the HTML ``form`` attribute.
ALLAUTH_FORM_ID = "daisie-allauth-form"

AUTH_FIELD_BLOCK_TYPE = "auth_field"
AUTH_FORM_BLOCK_TYPE = "auth_form"

AUTH_FIELD_PRESENTATION_CHOICES = ChoiceList(
    [
        ("", _("Default")),
        ("otp", _("One-time code")),
    ],
    "AUTH_FIELD_PRESENTATION_CHOICES",
)


class AllauthFieldBlock(blocks.StructBlock):
    """Render one allauth form field at this point in the body."""

    field = blocks.ChoiceBlock(
        choices=get_all_account_field_choices,
        help_text=_("An input from the account form for this page."),
    )
    label = blocks.CharBlock(
        required=False,
        blank=True,
        label=_("Label override"),
        help_text=_("Shown instead of the field's default label."),
    )
    help_text = blocks.CharBlock(
        required=False,
        blank=True,
        label=_("Help text override"),
    )
    placeholder = blocks.CharBlock(
        required=False,
        blank=True,
    )
    input_design = TypographyDesignBlock(
        required=False,
    )
    label_design = TypographyDesignBlock(
        required=False,
    )
    presentation = blocks.ChoiceBlock(
        choices=AUTH_FIELD_PRESENTATION_CHOICES,
        default="",
        required=False,
        help_text=_("Render as individual boxes for one-time codes."),
    )
    otp_size = blocks.ChoiceBlock(choices=OTP_SIZE_CHOICES, default="", required=False)
    otp_color = blocks.ChoiceBlock(
        choices=OTP_COLOR_CHOICES, default="", required=False
    )
    otp_joined = blocks.BooleanBlock(
        default=False, required=False, label=_("Join OTP boxes")
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        parent_context = parent_context or {}
        value = value or {}
        form = parent_context.get("form")
        name = value.get("field", "")
        bound_field = None
        if form is not None and name in getattr(form, "fields", {}):
            bound_field = form[name]
            if value.get("label"):
                bound_field.label = value["label"]
            if value.get("help_text"):
                bound_field.field.help_text = value["help_text"]
            if value.get("placeholder"):
                bound_field.field.widget.attrs["placeholder"] = value["placeholder"]
        context["bound_field"] = bound_field
        context["form_id"] = parent_context.get("form_id", ALLAUTH_FORM_ID)
        context["input_css"] = build_design_css(value.get("input_design"))
        context["label_css"] = build_design_css(value.get("label_design"))
        context["presentation"] = value.get("presentation", "")
        context["otp_size"] = value.get("otp_size", "")
        context["otp_color"] = value.get("otp_color", "")
        context["otp_joined"] = bool(value.get("otp_joined"))
        return context

    class Meta:
        icon = "form"
        label = _("Form field")
        collapsed = True
        template = "wagtail_daisIE/allauth/auth_field.html"
        form_layout = blocks.BlockGroup(
            children=[
                "field",
                "label",
                "help_text",
                "placeholder",
                "presentation",
                "otp_size",
                "otp_color",
                "otp_joined",
                "input_design",
                "label_design",
            ],
        )


class AllauthFormBlock(blocks.StructBlock):
    """Render the allauth form (and any unplaced fields) plus the submit."""

    submit_label = blocks.CharBlock(
        max_length=64,
        required=False,
        blank=True,
        help_text=_("Defaults to the allauth button label."),
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        parent_context = parent_context or {}
        form = parent_context.get("form")
        body = parent_context.get("body")
        placed = set(placed_field_names(body))
        visible = []
        if form is not None:
            visible = [
                field for name, field in form.fields.items() if name not in placed
            ]
        context["form"] = form
        context["form_id"] = ALLAUTH_FORM_ID
        context["hidden_fields"] = list(form.hidden_fields()) if form else []
        context["visible_fields"] = visible
        context["submit_label"] = (value or {}).get("submit_label", "")
        return context

    class Meta:
        icon = "form"
        label = _("Form")
        collapsed = True
        template = "wagtail_daisIE/allauth/auth_form.html"
        form_layout = blocks.BlockGroup(children=["submit_label"])


def placed_field_names(body):
    """Return the field names placed by ``auth_field`` blocks, in order."""
    if not body:
        return []
    return [
        child.value.get("field")
        for child in body
        if getattr(child, "block_type", None) == AUTH_FIELD_BLOCK_TYPE
        and hasattr(child.value, "get")
        and child.value.get("field")
    ]


#: The body block set for an allauth page override.
ALLAUTH_PAGE_BLOCKS = [
    *ALL_CONTENT_BLOCKS,
    (AUTH_FORM_BLOCK_TYPE, AllauthFormBlock()),
    (AUTH_FIELD_BLOCK_TYPE, AllauthFieldBlock()),
]


__all__ = [
    "ALLAUTH_FORM_ID",
    "ALLAUTH_PAGE_BLOCKS",
    "AllauthFieldBlock",
    "AllauthFormBlock",
    "placed_field_names",
]
