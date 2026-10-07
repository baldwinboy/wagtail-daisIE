"""Built-in ``account`` context value: allauth account URLs.

Exposes every ``allauth.account`` ("regular account") URL as a lazy,
defensive object so authors can link to sign-in, sign-up, password reset,
etc. from any content field or email template via ``{{ account.login_url }}``.

allauth is an optional dependency and is never imported here; URLs that are
unavailable (allauth absent, URL disabled by settings, or requiring arguments
that were not supplied) resolve to an empty string rather than raising.
"""

from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.urls import NoReverseMatch, reverse


#: Friendly attribute -> django-allauth reverse name.
ACCOUNT_URL_NAMES = {
    "login_url": "account_login",
    "logout_url": "account_logout",
    "signup_url": "account_signup",
    "inactive_url": "account_inactive",
    "reauthenticate_url": "account_reauthenticate",
    "email_url": "account_email",
    "email_verification_sent_url": "account_email_verification_sent",
    "change_password_url": "account_change_password",
    "set_password_url": "account_set_password",
    "password_reset_url": "account_reset_password",
    "reset_password_done_url": "account_reset_password_done",
    "reset_password_from_key_done_url": "account_reset_password_from_key_done",
    "request_login_code_url": "account_request_login_code",
    "confirm_login_code_url": "account_confirm_login_code",
    "confirm_password_reset_code_url": "account_confirm_password_reset_code",
    "complete_password_reset_url": "account_complete_password_reset",
    "password_reset_completed_url": "account_password_reset_completed",
    "change_phone_url": "account_change_phone",
    "verify_phone_url": "account_verify_phone",
    "signup_by_passkey_url": "account_signup_by_passkey",
}


class AccountURLs:
    """Lazily reversed allauth account URLs, optionally made absolute.

    :param request: current request, used to build absolute URLs.
    :param site: Wagtail ``Site`` fallback when no request is available.
    """

    def __init__(self, request=None, site=None):
        self._request = request
        self._site = site

    def _reverse(self, name, *args):
        try:
            path = reverse(name, args=args)
        except (NoReverseMatch, ImproperlyConfigured, TypeError, ValueError):
            return ""
        if not path:
            return ""
        if self._site is not None:
            base = getattr(self._site, "root_url", "") or ""
            if base:
                return f"{base.rstrip('/')}{path}"
            return path
        if self._request is not None:
            try:
                return self._request.build_absolute_uri(path)
            except (AttributeError, SuspiciousOperation, ValueError):
                return path
        return path

    def url(self, name):
        """Return the URL for a raw allauth reverse ``name``."""
        return self._reverse(name)

    @property
    def urls(self):
        """Return ``{friendly_name: url}`` for every known account URL."""
        return {
            friendly: self._reverse(name)
            for friendly, name in ACCOUNT_URL_NAMES.items()
        }

    def reset_password_from_key_url(self, uidb36, key):
        """URL for setting a new password from a reset link."""
        return self._reverse("account_reset_password_from_key", uidb36, key)

    def confirm_email_url(self, key):
        """URL for confirming an email address."""
        return self._reverse("account_confirm_email", key)

    def __getattr__(self, item):
        if item in ACCOUNT_URL_NAMES:
            return self._reverse(ACCOUNT_URL_NAMES[item])
        raise AttributeError(item)

    def __bool__(self):
        return True


def get_account_urls(request=None, site=None):
    """Return an :class:`AccountURLs` bound to ``request``/``site``."""
    return AccountURLs(request=request, site=site)
