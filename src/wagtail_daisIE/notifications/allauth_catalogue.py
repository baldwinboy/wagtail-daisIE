"""Discover the emails django-allauth can send, and their variables.

The catalogue is built by scanning the templates shipped by the installed
allauth apps, following ``{% extends %}``/``{% include %}`` so variables defined
in base templates are included. Curated labels are used where known; otherwise a
readable label is derived from the template prefix.

Discovery is lazy (never at import) and cached in-process.
"""

from __future__ import annotations

import logging
import re

from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path

from django.apps import apps
from django.utils.translation import gettext_lazy as _

from .placeholders import register_placeholder_provider


logger = logging.getLogger(__name__)

_VAR_RE = re.compile(r"{{\s*(?P<expr>.*?)\s*}}", re.DOTALL)
_TAG_RE = re.compile(r"{%\s*(?P<tag>\w+)(?P<rest>.*?)%}", re.DOTALL)
_INCLUDE_RE = re.compile(r"{%\s*(?:extends|include)\s+[\"'](?P<name>[^\"']+)[\"']")
_ROOT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_FILTERS = {
    "autoescape",
    "blocktrans",
    "blocktranslate",
    "endblocktrans",
    "endblocktranslate",
    "forloop",
    "include",
    "load",
    "static",
    "trans",
    "translate",
    "url",
    "with",
    "without",
}
_RESERVED = {
    "and",
    "as",
    "block",
    "blocktrans",
    "blocktranslate",
    "else",
    "elif",
    "empty",
    "endblock",
    "endfor",
    "endif",
    "endwith",
    "false",
    "for",
    "if",
    "in",
    "not",
    "none",
    "or",
    "true",
    "with",
}

#: Human labels for the emails we know about.
CURATED_LABELS = {
    "account/email/email_confirmation_signup": _("Signup email confirmation"),
    "account/email/email_confirmation": _("Email confirmation"),
    "account/email/email_confirm": _("Confirm email address"),
    "account/email/password_reset_key": _("Password reset"),
    "account/email/password_reset_code": _("Password reset code"),
    "account/email/password_reset": _("Password reset notification"),
    "account/email/password_changed": _("Password changed"),
    "account/email/password_set": _("Password set"),
    "account/email/email_changed": _("Email address changed"),
    "account/email/email_deleted": _("Email address deleted"),
    "account/email/login_code": _("Login code"),
    "account/email/unknown_account": _("Unknown account"),
    "account/email/account_already_exists": _("Account already exists"),
    "mfa/email/totp_activated": _("Authenticator app activated"),
    "mfa/email/totp_deactivated": _("Authenticator app deactivated"),
    "mfa/email/recovery_codes_generated": _("Recovery codes generated"),
    "mfa/email/webauthn_added": _("Security key added"),
    "mfa/email/webauthn_removed": _("Security key removed"),
    "socialaccount/email/account_connected": _("Social account connected"),
    "socialaccount/email/account_disconnected": _("Social account disconnected"),
}

_emails_cache: list[AllauthEmail] | None = None


@dataclass(frozen=True)
class AllauthEmail:
    """A single allauth email event and the variables it can use."""

    prefix: str
    label: object
    category: str
    variables: tuple[str, ...] = ()
    subject_path: str = ""
    message_path: str = ""
    files: tuple[str, ...] = field(default=())


def default_search_paths():
    """Return the ``templates`` directories of installed allauth apps/packages."""
    paths = []
    for config in apps.get_app_configs():
        if not (config.name == "allauth" or config.name.startswith("allauth.")):
            continue
        for candidate in (
            Path(config.path) / "templates",
            Path(config.path).parent / "templates",
        ):
            if candidate.is_dir() and candidate not in paths:
                paths.append(candidate)

    # allauth may be installed without being listed in INSTALLED_APPS; its
    # email templates still live in the package.
    for module_name in ("allauth",):
        try:
            module = import_module(module_name)
        except ImportError:
            continue
        candidate = Path(module.__file__).parent / "templates"
        if candidate.is_dir() and candidate not in paths:
            paths.append(candidate)
    return paths


def _read_template(path, base, seen, depth=0):
    """Return the concatenated text of a template and its base/includes."""
    if depth > 3:
        return ""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""
    chunks = [text]
    for match in _INCLUDE_RE.finditer(text):
        name = match.group("name")
        if name in seen:
            continue
        seen.add(name)
        candidate = base / name
        if candidate.is_file():
            chunks.append(_read_template(candidate, base, seen, depth + 1))
    return "\n".join(chunks)


def _extract_variables(text):
    found: list[str] = []

    def _add(name):
        if not name or name in _RESERVED or name in _FILTERS:
            return
        if name.lower() != name:
            return
        if name not in found:
            found.append(name)

    for match in _VAR_RE.finditer(text or ""):
        expression = match.group("expr").split("|", 1)[0]
        root = re.split(r"[.\[(]", expression.strip(), maxsplit=1)[0]
        _add(root.strip())

    for match in _TAG_RE.finditer(text or ""):
        tag = match.group("tag")
        if tag not in {"if", "elif", "for", "with", "blocktrans", "blocktranslate"}:
            continue
        for token in _ROOT_RE.findall(match.group("rest")):
            _add(token)
    return found


def _derive_label(prefix):
    return prefix.rsplit("/", 1)[-1].replace("_", " ").capitalize()


def discover_emails(search_paths=None, labels=None):
    """Return the discovered allauth emails, sorted by prefix."""
    paths = list(search_paths) if search_paths is not None else default_search_paths()
    label_map = {**CURATED_LABELS, **(labels or {})}
    entries: dict[str, dict] = {}

    for base_path in paths:
        base = Path(base_path)
        for subject in base.glob("**/email/*_subject.txt"):
            prefix = subject.relative_to(base).as_posix()[: -len("_subject.txt")]
            if prefix.rsplit("/", 1)[-1] == "base":
                continue
            entries.setdefault(prefix, {"base": base})["subject"] = subject
        for pattern in ("**/email/*_message.txt", "**/email/*_message.html"):
            for message in base.glob(pattern):
                prefix = re.sub(
                    r"_message\.(txt|html)$",
                    "",
                    message.relative_to(base).as_posix(),
                )
                if prefix.rsplit("/", 1)[-1] in {"base", "base_notification"}:
                    continue
                entries.setdefault(prefix, {"base": base})["message"] = message

    emails = []
    for prefix, data in entries.items():
        base = data["base"]
        subject = data.get("subject")
        message = data.get("message")
        seen: set[str] = set()
        text = ""
        files = []
        if message is not None:
            files.append(message.relative_to(base).as_posix())
            text += _read_template(message, base, seen)
        if subject is not None:
            files.append(subject.relative_to(base).as_posix())
            text += "\n" + _read_template(subject, base, seen)
        emails.append(
            AllauthEmail(
                prefix=prefix,
                label=label_map.get(prefix) or _derive_label(prefix),
                category=prefix.split("/", 1)[0],
                variables=tuple(sorted(_extract_variables(text))),
                subject_path=subject.relative_to(base).as_posix() if subject else "",
                message_path=message.relative_to(base).as_posix() if message else "",
                files=tuple(files),
            )
        )
    return sorted(emails, key=lambda email: email.prefix)


def get_allauth_emails(*, use_cache=True):
    """Return the cached catalogue of allauth emails."""
    global _emails_cache
    if use_cache and _emails_cache is not None:
        return _emails_cache
    try:
        _emails_cache = discover_emails()
    except Exception:  # pragma: no cover - defensive
        logger.exception("Could not discover allauth emails")
        _emails_cache = []
    return _emails_cache


def reset_allauth_emails():
    global _emails_cache
    _emails_cache = None


def get_allauth_email_choices():
    return [(email.prefix, email.label) for email in get_allauth_emails()]


def get_allauth_email(prefix):
    for email in get_allauth_emails():
        if email.prefix == prefix:
            return email
    return None


def get_allauth_placeholder_groups():
    """Placeholder groups (per category) for the admin help panel."""
    groups: dict[str, dict] = {}
    for email in get_allauth_emails():
        group = groups.setdefault(
            email.category,
            {
                "title": f"Allauth: {email.category}",
                "description": _(
                    "Variables available in allauth emails. Use them as {{ payload.<name> }}."
                ),
                "items": [],
            },
        )
        for name in email.variables:
            group["items"].append(
                {
                    "token": f"{{{{ payload.{name} }}}}",
                    "description": f"{email.label}: {name}",
                }
            )
    return list(groups.values())


register_placeholder_provider(get_allauth_placeholder_groups)
