"""Lazy discovery of django-allauth account views and their form fields.

Nothing here touches the database or imports allauth at module import time;
everything is resolved on first use, and missing/renamed allauth internals are
handled defensively. Only the ``account`` view set is exposed — see
``docs/allauth-pages.md`` for the rationale and the contribution path for other
view sets.

The form class for a view is resolved from the project's ``ACCOUNT_FORMS``
override first (matched by the allauth ``ACCOUNT_FORMS`` key), falling back to
the form allauth ships. Fields are read from a form *instance* where possible,
so fields allauth adds in ``__init__`` (``email2``, ``password1``,
``password2``, …) and project-added fields are included. Only the ``account``
view set is covered.
"""

from __future__ import annotations

import logging

from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)


#: account view name -> (label, dotted path to the fallback form class, key).
#:
#: ``key`` is the matching ``ACCOUNT_FORMS`` key; when the project configures
#: that key the configured form class is used instead of the dotted path. The
#: form is introspected lazily for its fields. Views without a form (logout,
#: inactive, done pages) are still listed so an override can restyle the page,
#: but expose no fields.
ACCOUNT_VIEWS: dict[str, tuple[object, str, str]] = {
    "account_login": (_("Sign in"), "allauth.account.forms.LoginForm", "login"),
    "account_signup": (_("Sign up"), "allauth.account.forms.SignupForm", "signup"),
    "account_logout": (_("Sign out"), "", ""),
    "account_inactive": (_("Account inactive"), "", ""),
    "account_email": (
        _("Email addresses"),
        "allauth.account.forms.AddEmailForm",
        "add_email",
    ),
    "account_change_password": (
        _("Change password"),
        "allauth.account.forms.ChangePasswordForm",
        "change_password",
    ),
    "account_set_password": (
        _("Set password"),
        "allauth.account.forms.SetPasswordForm",
        "set_password",
    ),
    "account_reset_password": (
        _("Reset password"),
        "allauth.account.forms.ResetPasswordForm",
        "reset_password",
    ),
    "account_reset_password_done": (_("Reset password sent"), "", ""),
    "account_reset_password_from_key": (
        _("Set new password"),
        "allauth.account.forms.ResetPasswordKeyForm",
        "reset_password_from_key",
    ),
    "account_reset_password_from_key_done": (_("Password changed"), "", ""),
    "account_reauthenticate": (
        _("Confirm access"),
        "allauth.account.forms.ReauthenticateForm",
        "reauthenticate",
    ),
    "account_request_login_code": (
        _("Request login code"),
        "allauth.account.forms.RequestLoginCodeForm",
        "request_login_code",
    ),
    "account_confirm_login_code": (
        _("Confirm login code"),
        "allauth.account.forms.ConfirmLoginCodeForm",
        "confirm_login_code",
    ),
    "account_email_verification_sent": (_("Verification sent"), "", ""),
    "account_confirm_password_reset_code": (
        _("Confirm reset code"),
        "allauth.account.forms.ConfirmPasswordResetCodeForm",
        "confirm_password_reset_code",
    ),
    "account_change_phone": (
        _("Change phone"),
        "allauth.account.forms.ChangePhoneForm",
        "change_phone",
    ),
}


#: Fields that are never offered to authors: allauth's captcha and the signup
#: honeypot are implementation details, not author-controllable inputs.
_ALWAYS_EXCLUDED_FIELDS = frozenset({"captcha"})

#: Per-view cache of resolved field choices. Cleared by :func:`clear_cache`.
_CHOICES_CACHE: dict[str, list[tuple[str, str]]] = {}


def get_allauth_view_choices():
    """Return ``[(view_name, label), ...]`` for the account view set."""
    return [(name, entry[0]) for name, entry in ACCOUNT_VIEWS.items()]


def _configured_form_path(key):
    """Return the ``ACCOUNT_FORMS`` override path for ``key``, or ``None``."""
    if not key:
        return None
    try:
        from allauth.account import app_settings as account_settings
    except ImportError:  # pragma: no cover - allauth is optional
        return None
    return account_settings.FORMS.get(key)


def _resolve_form_class(view):
    entry = ACCOUNT_VIEWS.get(view)
    if not entry:
        return None
    _label, fallback_path, key = entry
    for path in (_configured_form_path(key), fallback_path):
        if not path:
            continue
        try:
            return import_string(path)
        except ImportError:
            logger.warning("Could not import allauth form %r", path)
    return None


def _form_fields(form_class):
    """Return the field mapping for a form class.

    Prefers a form *instance* so fields added in ``__init__`` (``email2``,
    ``password1``, ``password2``, project fields, …) are included; forms that
    require constructor arguments fall back to the class-level ``base_fields``.
    """
    try:
        return form_class().fields
    except Exception:
        logger.debug(
            "Could not instantiate %r for field discovery", form_class, exc_info=True
        )
    try:
        return form_class.base_fields
    except Exception:  # pragma: no cover - defensive
        return {}


def _excluded_field_names(view):
    """Return the field names hidden from the picker for ``view``."""
    excluded = set(_ALWAYS_EXCLUDED_FIELDS)
    if view == "account_signup":
        honeypot = _signup_honeypot_field()
        if honeypot:
            excluded.add(honeypot)
    return excluded


def _signup_honeypot_field():
    try:
        from allauth.account import app_settings as account_settings
    except ImportError:  # pragma: no cover - allauth is optional
        return None
    return account_settings.SIGNUP_FORM_HONEYPOT_FIELD


def clear_cache():
    """Clear the cached field choices (used after settings changes/tests)."""
    _CHOICES_CACHE.clear()


def get_allauth_field_choices(view):
    """Return ``[(field_name, label), ...]`` for ``view``'s form, or ``[]``."""
    if view in _CHOICES_CACHE:
        return _CHOICES_CACHE[view]
    form_class = _resolve_form_class(view)
    if form_class is None:
        _CHOICES_CACHE[view] = []
        return []
    excluded = _excluded_field_names(view)
    choices = []
    for name, field in _form_fields(form_class).items():
        if name in excluded:
            continue
        label = field.label or name.replace("_", " ").title()
        choices.append((name, str(label)))
    _CHOICES_CACHE[view] = choices
    return choices


def get_all_account_field_choices():
    """Return a de-duplicated ``[(name, label), ...]`` across account forms.

    The field picker on an ``auth_field`` block is intentionally view-agnostic
    (a block cannot see its parent snippet's ``view``), so the choices are the
    union of every account form's fields. Matching happens by field name at
    render time.
    """
    choices = []
    seen = set()
    for name in ACCOUNT_VIEWS:
        for field_name, label in get_allauth_field_choices(name):
            if field_name in seen:
                continue
            seen.add(field_name)
            choices.append((field_name, label))
    return choices


def sample_form(view):
    """Return an unbound sample form instance for ``view``, or ``None``.

    Used only to render admin previews; allauth forms that require constructor
    arguments fall back to ``None``.
    """
    form_class = _resolve_form_class(view)
    if form_class is None:
        return None
    try:
        return form_class()
    except Exception:  # pragma: no cover - forms needing args/kwargs
        logger.debug("Could not build sample form for %r", view, exc_info=True)
        return None


__all__ = [
    "ACCOUNT_VIEWS",
    "clear_cache",
    "get_allauth_field_choices",
    "get_allauth_view_choices",
    "get_all_account_field_choices",
    "sample_form",
]
