"""Curated context values offered to the dynamic-link editor control.

The dynamic-link control (``draftail_text_utils``) accepts a host-supplied
``window.draftailTextUtils.dynamicLinkContext`` list of groups. This module
builds the curated groups (account URLs, the site root, and each configured
context model) and then appends the broader placeholder groups, de-duplicated.

Everything is derived from settings/registry data, so no database changes or
migrations are involved.
"""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _


def _account_group():
    return {
        "title": _("Account"),
        "description": _("django-allauth account URLs"),
        "items": [
            {
                "token": "{{ account.login_url }}",
                "description": _("Sign-in page."),
            },
            {
                "token": "{{ account.signup_url }}",
                "description": _("Sign-up page."),
            },
            {
                "token": "{{ account.password_reset_url }}",
                "description": _("Request a password reset."),
            },
            {
                "token": "{{ account.logout_url }}",
                "description": _("Sign-out URL."),
            },
        ],
    }


def _site_group():
    return {
        "title": _("Site"),
        "items": [
            {
                "token": "{{ site.root_url }}",
                "description": _("Base URL of the current site."),
            },
        ],
    }


def _context_model_groups():
    from .registry import get_context_models

    groups = []
    for key, config in get_context_models().items():
        items = [
            {
                "token": f"{{{{ {key} }}}}",
                "description": _("The resolved value, if any."),
            }
        ]
        if config.url_source or config.supports_url:
            items.append(
                {
                    "token": f"{{{{ {key}.url }}}}",
                    "description": _("URL derived from the model's url_source."),
                }
            )
        for doc in config.field_docs(limit=12):
            items.append(
                {
                    "token": f"{{{{ {key}.{doc['name']} }}}}",
                    "description": doc["label"],
                }
            )
        model = config.model
        groups.append(
            {
                "title": str(config.label),
                "description": model._meta.label if model else config.model_path,
                "items": items,
            }
        )
    return groups


def get_dynamic_link_context():
    """Return the curated dynamic-link groups (account, site, context models)."""
    return [_account_group(), _site_group(), *_context_model_groups()]


def _dedupe(groups, seen):
    result = []
    for group in groups:
        items = []
        for item in group.get("items", ()):
            token = item.get("token")
            if not token or token in seen:
                continue
            seen.add(token)
            items.append(item)
        if items:
            result.append({**group, "items": items})
    return result


def get_dynamic_link_groups():
    """Return curated groups followed by the broader placeholder groups."""
    seen: set[str] = set()
    groups = _dedupe(get_dynamic_link_context(), seen)
    try:
        from ..notifications.placeholders import get_placeholder_groups

        groups.extend(_dedupe(get_placeholder_groups(), seen))
    except ImportError:  # pragma: no cover - notifications app optional
        pass
    return groups
