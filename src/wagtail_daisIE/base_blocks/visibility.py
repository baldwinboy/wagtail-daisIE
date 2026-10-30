"""Shared block visibility controls.

A block can be controlled by a page/in-context switch, by a server-side
condition against a configured context model, or by both. Switch visibility is
CSS-only; context conditions are evaluated before rendering.
"""

from __future__ import annotations

import logging

from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from .compact import DaisieStructBlock
from .form_layout import collapsed_group


logger = logging.getLogger(__name__)

MAX_SWITCH_KEY_LENGTH = 64


def _context_model_choices():
    from ..dynamic.registry import get_context_model_choices

    return get_context_model_choices()


def _context_field_choices():
    from ..dynamic.registry import get_context_models

    groups = []
    for _key, config in get_context_models().items():
        fields = config.field_docs(limit=None)
        if fields:
            groups.append(
                (
                    str(config.label),
                    [(field["name"], field["label"]) for field in fields],
                )
            )
    return groups


def _operator_choices():
    from ..dynamic.conditions import FEED_CONDITION_OPERATOR_CHOICES

    return FEED_CONDITION_OPERATOR_CHOICES


def _rule_choices():
    from ..dynamic.conditions import get_feed_condition_choices

    return get_feed_condition_choices()


def _as_mapping(value):
    return value if hasattr(value, "get") else {}


def _condition_value(condition, key):
    return str(_as_mapping(condition).get(key) or "").strip()


def _condition_expression(condition):
    expression = _condition_value(condition, "expression")
    if expression:
        return expression
    model = _condition_value(condition, "context_model")
    field = _condition_value(condition, "field_name")
    if model and field:
        return f"{model}.{field}"
    return ""


def _needs_compare_value(operator: str) -> bool:
    from ..dynamic.conditions import CUSTOM_OPERATOR

    return bool(operator) and operator not in {"is_true", "is_false", CUSTOM_OPERATOR}


def _validate_slug_key(key: str, label: object) -> str:
    key = (key or "").strip()
    if not key:
        return ""
    if len(key) > MAX_SWITCH_KEY_LENGTH:
        raise ValidationError(
            _("%(label)s keys must be 64 characters or fewer."),
            params={"label": label},
        )
    try:
        validate_slug(key)
    except ValidationError as exc:
        raise ValidationError(
            _(
                "%(label)s keys may only contain letters, numbers, hyphens "
                "and underscores."
            ),
            params={"label": label},
        ) from exc
    return key


class ContextConditionBlock(DaisieStructBlock):
    """A model-aware condition builder for non-technical editors."""

    context_model = blocks.ChoiceBlock(
        choices=_context_model_choices,
        required=False,
        blank=True,
        label=_("Context"),
        help_text=_("Choose a configured context value."),
        form_attrs={
            "data-daisie-visibility-condition-target": "contextModel",
        },
    )
    field_name = blocks.ChoiceBlock(
        choices=_context_field_choices,
        required=False,
        blank=True,
        label=_("Property"),
        help_text=_("Choose the property to compare."),
        form_attrs={
            "data-daisie-visibility-condition-target": "fieldName",
        },
    )
    operator = blocks.ChoiceBlock(
        choices=_operator_choices,
        default="equals",
        required=False,
        label=_("Comparison"),
        form_attrs={
            "data-daisie-visibility-condition-target": "operator",
        },
    )
    compare_value = blocks.CharBlock(
        required=False,
        blank=True,
        label=_("Value"),
        help_text=_("For 'is one of', separate values with commas."),
        form_attrs={
            "data-daisie-visibility-condition-target": "compareValue",
        },
    )
    rule = blocks.ChoiceBlock(
        choices=_rule_choices,
        required=False,
        label=_("Custom rule"),
        help_text=_(
            "Used when the comparison is 'matches a custom rule'. Registered in "
            "WAGTAIL_DAISIE_FEED_CONDITIONS."
        ),
        form_attrs={
            "data-daisie-visibility-condition-target": "rule",
        },
    )
    invert = blocks.BooleanBlock(
        default=False,
        required=False,
        label=_("Show only when this is not true"),
    )
    expression = blocks.CharBlock(
        required=False,
        blank=True,
        label=_("Advanced expression"),
        help_text=_(
            "Developer use only. A dotted path such as meeting.status. "
            "Use instead of the dropdown selections."
        ),
        form_attrs={
            "data-daisie-visibility-condition-target": "expression",
        },
    )

    def clean(self, value):
        from ..dynamic.conditions import CUSTOM_OPERATOR

        value = super().clean(value)
        model = _condition_value(value, "context_model")
        field = _condition_value(value, "field_name")
        operator = _condition_value(value, "operator")
        rule = _condition_value(value, "rule")
        expression = _condition_value(value, "expression")
        compare_value = _condition_value(value, "compare_value")

        if expression:
            if model or field:
                raise ValidationError(
                    _(
                        "Use either the context/property picker or an advanced "
                        "expression, not both."
                    )
                )
            if rule:
                raise ValidationError(
                    _("An advanced expression cannot be combined with a custom rule.")
                )
            if not operator:
                raise ValidationError(_("Choose a comparison."))
            if operator == CUSTOM_OPERATOR:
                raise ValidationError(
                    _("A custom rule needs a rule selected, not an expression.")
                )
            if _needs_compare_value(operator) and not compare_value:
                raise ValidationError(_("Enter a value to compare against."))
            return value

        if rule:
            if operator != CUSTOM_OPERATOR:
                raise ValidationError(
                    _(
                        "Choose the 'matches a custom rule' comparison when "
                        "selecting a custom rule."
                    )
                )
            if model or field:
                raise ValidationError(
                    _("A custom rule cannot be combined with a context property.")
                )
            return value

        if model or field:
            if not (model and field):
                raise ValidationError(
                    _("Choose both a context value and a property, or neither.")
                )
            from ..dynamic.registry import get_context_model

            config = get_context_model(model)
            if config is None:
                raise ValidationError(
                    _("The selected context value is not configured.")
                )
            field_names = {doc["name"] for doc in config.field_docs(limit=None)}
            if field not in field_names:
                raise ValidationError(
                    _("The selected property does not exist on this context value.")
                )
            if not operator:
                raise ValidationError(_("Choose a comparison."))
            if operator == CUSTOM_OPERATOR:
                raise ValidationError(_("Choose a custom rule."))
            if _needs_compare_value(operator) and not compare_value:
                raise ValidationError(_("Enter a value to compare against."))
            return value

        if operator == CUSTOM_OPERATOR:
            raise ValidationError(_("Choose a custom rule."))
        if compare_value:
            raise ValidationError(
                _("Choose a context value and property, or clear the value.")
            )

        return value

    class Meta:
        icon = "cog"
        label = _("Context condition")
        collapsed = True
        form_attrs = {
            "data-controller": "daisie-visibility-condition",
            "data-action": (
                "change->daisie-visibility-condition#refresh "
                "input->daisie-visibility-condition#refresh"
            ),
        }
        form_layout = blocks.BlockGroup(
            children=[
                "context_model",
                "field_name",
                "operator",
                "compare_value",
                "rule",
                "invert",
                collapsed_group(_("Advanced"), "expression", icon="code"),
            ],
            heading=_("Only show when the data matches"),
        )


class VisibilityBlock(DaisieStructBlock):
    """Visibility settings shared by target blocks."""

    switch_key = blocks.CharBlock(
        max_length=MAX_SWITCH_KEY_LENGTH,
        required=False,
        blank=True,
        validators=[validate_slug],
        label=_("Control key"),
        help_text=_(
            "Match a Toggle or Swap block on this page. Leave empty for no "
            "switch condition."
        ),
        form_attrs={
            "data-daisie-switch-key-target": "switchKey",
        },
    )
    show_when = blocks.BooleanBlock(
        default=True,
        required=False,
        label=_("Show when the switch is on"),
        help_text=_("Untick to show only when the switch is off."),
    )
    condition = ContextConditionBlock(required=False)

    class Meta:
        icon = "cog"
        label = _("Visibility")
        collapsed = True
        form_attrs = {
            "data-controller": "daisie-switch-key",
            "data-action": "input@window->daisie-switch-key#refresh",
        }
        form_layout = blocks.BlockGroup(
            children=[
                collapsed_group(
                    _("Controlled by a switch"),
                    "switch_key",
                    "show_when",
                    icon="cog",
                ),
                "condition",
            ],
            heading=_("Visibility"),
        )


def context_condition_allows(visibility, context) -> bool:
    """Return whether the server-side context condition passes."""
    from ..dynamic.conditions import CUSTOM_OPERATOR, evaluate_condition
    from ..dynamic.resolvers import resolve_object

    visibility = _as_mapping(visibility)
    condition = _as_mapping(visibility.get("condition"))
    expression = _condition_expression(condition)
    operator = _condition_value(condition, "operator")
    rule = _condition_value(condition, "rule")
    compare_value = _condition_value(condition, "compare_value")
    invert = bool(condition.get("invert"))
    has_any = any(
        _condition_value(condition, key)
        for key in ("context_model", "field_name", "expression", "rule")
    )
    if not has_any and not compare_value:
        return True

    if operator == CUSTOM_OPERATOR:
        if not rule:
            logger.warning("Visibility custom rule is missing a rule key")
            return False
        obj = resolve_object(expression, context) if expression else None
        return evaluate_condition(
            {"operator": CUSTOM_OPERATOR, "rule": rule},
            obj,
            context,
            invert=invert,
        )

    if not expression:
        logger.warning("Visibility condition has no context expression")
        return False
    if _needs_compare_value(operator) and not compare_value:
        logger.warning("Visibility condition %r has no compare value", expression)
        return False

    return evaluate_condition(
        {
            "expression": expression,
            "operator": operator,
            "compare_value": compare_value,
        },
        None,
        context,
        missing_is_false=True,
        invert=invert,
    )


class VisibilityMixin:
    """Render a switch wrapper and evaluate context conditions."""

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        if "visibility" not in self.child_blocks:
            return context
        from ..dynamic.context import copy_context_values

        copy_context_values(parent_context, context)
        return context

    def render(self, value, context=None):
        if "visibility" not in self.child_blocks:
            return super().render(value, context)

        visibility = _as_mapping(_as_mapping(value).get("visibility"))
        if not context_condition_allows(visibility, context or {}):
            return ""

        html = super().render(value, context)
        if html is None:
            return ""
        if not str(html).strip():
            return html

        key = str(visibility.get("switch_key") or "").strip()
        if not key:
            return html

        state = "on" if visibility.get("show_when", True) else "off"
        return format_html(
            '<daisie-visibility class="daisie-visibility-target" '
            'data-daisie-visibility-key="{}" '
            'data-daisie-visibility-state="{}" role="none">{}</daisie-visibility>',
            key,
            state,
            mark_safe(str(html)),  # noqa: S308 - block output is already escaped
        )


def build_switch_css(key: str, scope: str = "") -> str:
    """Return per-controller CSS for a validated switch key."""
    key = (key or "").strip()
    if not key:
        return ""
    try:
        validate_slug(key)
    except ValidationError:
        logger.warning("Ignoring invalid visibility key %r", key)
        return ""
    if len(key) > MAX_SWITCH_KEY_LENGTH:
        return ""

    scope = (scope or "").strip()
    scope_attr = ""
    container = ""
    if scope in {"feed-item", "calendar-event", "menu"}:
        scope_attr = f'[data-daisie-switch-scope="{scope}"]'
        container = {
            "feed-item": "[data-daisie-feed-item]",
            "calendar-event": "[data-daisie-calendar-event]",
            "menu": "[data-daisie-menu]",
        }[scope]
    controller = f'[data-daisie-switch-key="{key}"]{scope_attr}'
    if container:
        controller_scope = f"{container}:has({controller}:checked)"
    else:
        controller_scope = (
            f'body:has([data-daisie-switch-key="{key}"]'
            ":not([data-daisie-switch-scope]):checked)"
        )

    target = f'.daisie-visibility-target[data-daisie-visibility-key="{key}"]'
    return (
        "@supports selector(:has(*)) {"
        f'{controller_scope} {target}[data-daisie-visibility-state="on"],'
        f"{controller_scope.replace(':checked)', ':not(:checked))')} "
        f'{target}[data-daisie-visibility-state="off"]'
        "{display:contents}"
        "}"
    )


def _is_calendar_event_stream(key, child, parent):
    return key == "event" and "context_model" in parent and "date_field" in parent


def iter_visibility_entries(value, _seen_reusable=None):
    """Yield every struct/dict value relevant to visibility validation."""
    from ..dynamic.recursion import iter_nested_stream_blocks

    seen_reusable = _seen_reusable or set()
    seen_values = set()
    for _block_type, item in iter_nested_stream_blocks(
        value,
        include_structs=True,
        skip=_is_calendar_event_stream,
    ):
        if not hasattr(item, "get"):
            continue
        marker = id(item)
        if marker in seen_values:
            continue
        seen_values.add(marker)
        yield item
        reusable = item.get("reusable")
        if reusable is None:
            continue
        content = getattr(reusable, "content", None)
        if not content:
            continue
        marker = getattr(reusable, "pk", None) or id(reusable)
        if marker in seen_reusable:
            continue
        yield from iter_visibility_entries(
            content,
            _seen_reusable={*seen_reusable, marker},
        )


def validate_visibility_stream(stream, label) -> None:
    """Validate controller-key uniqueness and key formats in ``stream``."""
    controllers = []
    for item in iter_visibility_entries(stream):
        logic_key = str(item.get("logic_key") or "").strip()
        if logic_key:
            _validate_slug_key(logic_key, label)
            controllers.append(logic_key)
        visibility = _as_mapping(item.get("visibility"))
        switch_key = str(visibility.get("switch_key") or "").strip()
        if switch_key:
            _validate_slug_key(switch_key, label)

    duplicates = sorted({key for key in controllers if controllers.count(key) > 1})
    if duplicates:
        raise ValidationError(
            _(
                "%(label)s uses the same logic key more than once: %(keys)s. "
                "Logic keys must be unique within the same rendered scope."
            ),
            params={"label": label, "keys": ", ".join(duplicates)},
        )


__all__ = [
    "ContextConditionBlock",
    "MAX_SWITCH_KEY_LENGTH",
    "VisibilityBlock",
    "VisibilityMixin",
    "build_switch_css",
    "context_condition_allows",
    "iter_visibility_entries",
    "validate_visibility_stream",
]
