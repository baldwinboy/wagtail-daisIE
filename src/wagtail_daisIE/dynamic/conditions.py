"""Conditions evaluated against a rendered context.

Simple comparisons use a dotted expression resolved with the same safe,
attribute-only lookups as dynamic links; anything more complex is delegated to
a named rule registered in ``WAGTAIL_DAISIE_FEED_CONDITIONS`` -- the same
settings-driven bridge shape as ``WAGTAIL_DAISIE_AUDIENCE_RULES``.

Rules are dotted paths to callables (or callables themselves) that receive the
resolved object and the current request and return truthy on a match. Missing
rules and raised errors are treated as "no match" so a broken condition never
takes down a page.
"""

from __future__ import annotations

import inspect
import logging

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from ..choicelist import ChoiceList
from .resolvers import resolve_object


logger = logging.getLogger(__name__)

#: Operator key that delegates to a named, settings-registered rule.
CUSTOM_OPERATOR = "custom"

#: Basic operators evaluated against the resolved expression value.
FEED_CONDITION_OPERATOR_CHOICES = ChoiceList(
    [
        ("is_true", _("is true")),
        ("is_false", _("is false")),
        ("equals", _("equals")),
        ("not_equals", _("does not equal")),
        ("in", _("is one of")),
        ("not_in", _("is not one of")),
        ("contains", _("contains")),
        ("starts_with", _("starts with")),
        ("gt", _("is greater than")),
        ("gte", _("is greater than or equal to")),
        ("lt", _("is less than")),
        ("lte", _("is less than or equal to")),
        (CUSTOM_OPERATOR, _("matches a custom rule")),
    ],
    "FEED_CONDITION_OPERATOR_CHOICES",
)


def get_feed_condition_choices():
    """Choices for :data:`CUSTOM_OPERATOR`, from the configured rules."""
    return [
        (key, config.get("label", key))
        for key, config in getattr(
            settings, "WAGTAIL_DAISIE_FEED_CONDITIONS", {}
        ).items()
    ]


def get_feed_condition_rule(key):
    """Return the raw config for a named condition key, or ``None``."""
    rules = getattr(settings, "WAGTAIL_DAISIE_FEED_CONDITIONS", {})
    return rules.get(key)


def _resolve_rule(config):
    rule = (config or {}).get("rule")
    if not rule:
        return None
    if callable(rule):
        return rule
    try:
        return import_string(rule)
    except ImportError as exc:
        logger.warning("Could not resolve feed condition %r: %s", rule, exc)
        return None


def _call_rule(rule, obj, request):
    """Call a rule with ``(obj, request)`` or ``(obj)``.

    The arity is detected from the signature where possible so a ``TypeError``
    raised *inside* a rule is not mistaken for a wrong signature (and silently
    retried). Fallible signatures (builtins, partials) still fall back.
    """
    try:
        parameters = inspect.signature(rule).parameters
    except (TypeError, ValueError):
        parameters = None
    if parameters is not None:
        positional = [
            param
            for param in parameters.values()
            if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD)
        ]
        variadic = any(
            param.kind == param.VAR_POSITIONAL for param in parameters.values()
        )
        if variadic or len(positional) >= 2:
            return rule(obj, request)
        return rule(obj)
    try:
        return rule(obj, request)
    except TypeError:
        return rule(obj)


def evaluate_custom_condition(key, obj, request, *, invert=False):
    """Evaluate a named, settings-registered condition for ``obj``."""
    rule = _resolve_rule(get_feed_condition_rule(key))
    if rule is None:
        return False
    try:
        allowed = bool(_call_rule(rule, obj, request))
    except Exception:
        logger.exception("Feed condition %r raised while evaluating", key)
        return False
    return not allowed if invert else allowed


def _coerce(value, sample):
    """Coerce the admin-entered string ``value`` to the resolved value's type."""
    if isinstance(sample, bool):
        return str(value).strip().lower() in ("1", "true", "yes", "on")
    if isinstance(sample, int):
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None
    if isinstance(sample, float):
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return None
    if isinstance(sample, Decimal):
        try:
            return Decimal(str(value).strip())
        except (TypeError, InvalidOperation):
            return None
    if isinstance(sample, datetime):
        try:
            parsed = datetime.fromisoformat(str(value).strip())
        except (TypeError, ValueError):
            return None
        # Avoid naive/aware comparison errors when the model value is aware.
        if sample.tzinfo is not None and parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=sample.tzinfo)
        return parsed
    if isinstance(sample, date):
        try:
            return date.fromisoformat(str(value).strip())
        except (TypeError, ValueError):
            return None
    return "" if value is None else str(value)


def _compare(resolved, operator, value):
    if operator == "is_true":
        return bool(resolved)
    if operator == "is_false":
        return not bool(resolved)
    if operator in ("in", "not_in"):
        parts = [part.strip() for part in str(value).split(",") if part.strip()]
        expected = [_coerce(part, resolved) for part in parts]
        matched = resolved in expected
        return matched if operator == "in" else not matched
    if operator == "contains":
        return resolved is not None and str(value) in str(resolved)
    if operator == "starts_with":
        return resolved is not None and str(resolved).startswith(str(value))
    expected = _coerce(value, resolved)
    if expected is None:
        return False
    if operator == "equals":
        return resolved == expected
    if operator == "not_equals":
        return resolved != expected
    if operator == "gt":
        return resolved > expected
    if operator == "gte":
        return resolved >= expected
    if operator == "lt":
        return resolved < expected
    if operator == "lte":
        return resolved <= expected
    return False


_OPERATOR_KEYS = frozenset(key for key, _label in FEED_CONDITION_OPERATOR_CHOICES)


def evaluate_condition(
    value,
    obj,
    context,
    *,
    missing_is_false=False,
    invert=False,
):
    """Return whether a condition matches ``obj``.

    An empty expression matches every item (a catch-all). Any failure to resolve
    or compare is treated as "no match". ``missing_is_false`` makes an
    unresolved expression fail closed. ``invert`` is applied only after a
    successful comparison, so invalid or missing values never become visible
    through inversion.
    """
    value = value or {}
    operator = (value.get("operator") or "").strip()
    request = context.get("request") if hasattr(context, "get") else None

    if operator == CUSTOM_OPERATOR:
        key = (value.get("rule") or "").strip()
        return (
            evaluate_custom_condition(key, obj, request, invert=invert)
            if key
            else False
        )

    if operator not in _OPERATOR_KEYS:
        logger.warning("Ignoring unknown condition operator %r", operator)
        return False

    expression = (value.get("expression") or "").strip()
    if not expression:
        return True
    try:
        resolved = resolve_object(expression, context)
        if missing_is_false and resolved is None:
            return False
        allowed = _compare(resolved, operator, value.get("compare_value"))
    except Exception:
        logger.warning("Ignoring invalid condition %r", expression, exc_info=True)
        return False
    return not allowed if invert else allowed
