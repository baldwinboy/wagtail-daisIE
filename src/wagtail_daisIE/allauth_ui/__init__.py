"""Opt-in DaisyUI styling for django-allauth pages and forms.

When ``WAGTAIL_DAISIE_ALLAUTH_UI`` is enabled, the directory
``wagtail_daisIE/allauth_ui/templates`` is prepended to the project's Django
template ``DIRS`` so its overrides of allauth's layouts and form elements take
effect. When disabled, allauth's own templates are used untouched.
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings


DJANGO_TEMPLATES_BACKEND = "django.template.backends.django.DjangoTemplates"


def template_dir():
    """Return the absolute path to the bundled allauth override templates."""
    return str(Path(__file__).resolve().parent / "templates")


def register_template_dir(templates=None):
    """Prepend the override templates to every Django template engine.

    Idempotent. Pass ``templates`` to operate on a specific engine list (used by
    tests); otherwise ``settings.TEMPLATES`` is used.
    """
    target = template_dir()
    engines = (
        templates if templates is not None else getattr(settings, "TEMPLATES", None)
    )
    if not engines:
        return False

    registered = False
    for engine in engines:
        if engine.get("BACKEND") != DJANGO_TEMPLATES_BACKEND:
            continue
        dirs = list(engine.get("DIRS") or [])
        if target in dirs:
            continue
        engine["DIRS"] = [target, *dirs]
        registered = True
    return registered
