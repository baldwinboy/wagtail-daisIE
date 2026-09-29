"""Lazy discovery of django-allauth account views and their form fields.

Nothing here touches the database or imports allauth at module import time;
everything is resolved on first use, and missing/renamed allauth internals are
handled defensively. Only the ``account`` view set is exposed — see
``docs/allauth-pages.md`` for the rationale and the contribution path for other
view sets.
"""

from __future__ import annotations

import logging

from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)


#: account view name -> (label, dotted path to the form class or "").
#:
#: The form path is introspected lazily for its fields. Views without a form
#: (logout, inactive, done pages) are still listed so an override can restyle
#: the page, but expose no fields.
ACCOUNT_VIEWS: dict[str, tuple[object, str]] = {
    "account_login": (_("Sign in"), "allauth.account.forms.LoginForm"),
    "account_signup": (_("Sign up"), "allauth.account.forms.SignupForm"),
    "account_logout": (_("Sign out"), ""),
    "account_inactive": (_("Account inactive"), ""),
    "account_email": (_("Email addresses"), "allauth.account.forms.AddEmailForm"),
    "account_change_password": (
        _("Change password"),
        "allauth.account.forms.ChangePasswordForm",
    ),
    "account_set_password": (
        _("Set password"),
        "allauth.account.forms.SetPasswordForm",
    ),
    "account_reset_password": (
        _("Reset password"),
        "allauth.account.forms.ResetPasswordForm",
    ),
    "account_reset_password_done": (_("Reset password sent"), ""),
    "account_reset_password_from_key": (
        _("Set new password"),
        "allauth.account.forms.ResetPasswordKeyForm",
    ),
    "account_reset_password_from_key_done": (_("Password changed"), ""),
    "account_reauthenticate": (
        _("Confirm access"),
        "allauth.account.forms.ReauthenticateForm",
    ),
    "account_request_login_code": (
        _("Request login code"),
        "allauth.account.forms.RequestLoginCodeForm",
    ),
    "account_confirm_login_code": (
        _("Confirm login code"),
        "allauth.account.forms.ConfirmLoginCodeForm",
    ),
    "account_email_verification_sent": (_("Verification sent"), ""),
    "account_confirm_password_reset_code": (
        _("Confirm reset code"),
        "allauth.account.forms.ConfirmPasswordResetCodeForm",
    ),
    "account_change_phone": (
        _("Change phone"),
        "allauth.account.forms.ChangePhoneForm",
    ),
}


def get_allauth_view_choices():
    """Return ``[(view_name, label), ...]`` for the account view set."""
    return [(name, label) for name, (label, _path) in ACCOUNT_VIEWS.items()]


def _resolve_form_class(view):
    entry = ACCOUNT_VIEWS.get(view)
    if not entry:
        return None
    path = entry[1]
    if not path:
        return None
    try:
        return import_string(path)
    except ImportError:
        logger.warning("Could not import allauth form %r", path)
        return None


def get_allauth_field_choices(view):
    """Return ``[(field_name, label), ...]`` for ``view``'s form, or ``[]``."""
    form_class = _resolve_form_class(view)
    if form_class is None:
        return []
    try:
        base_fields = form_class.base_fields
    except Exception:  # pragma: no cover - defensive
        return []
    choices = []
    for name, field in base_fields.items():
        if name in ("captcha",):
            continue
        label = field.label or name.replace("_", " ").title()
        choices.append((name, str(label)))
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
    "get_allauth_field_choices",
    "get_allauth_view_choices",
    "get_all_account_field_choices",
    "sample_form",
]
