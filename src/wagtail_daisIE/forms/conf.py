"""Settings accessors for the form field-type registry."""

from django.conf import settings


FIELD_TYPES_SETTING = "WAGTAIL_DAISIE_FORM_FIELD_TYPES"
UPLOAD_HANDLER_SETTING = "WAGTAIL_DAISIE_FORM_UPLOAD_HANDLER"


def get_field_type_config():
    """Return the configured form field types (never touches the database)."""
    return getattr(settings, FIELD_TYPES_SETTING, {}) or {}


def get_default_upload_handler_path():
    """Return the dotted path of the project-wide upload handler, if any."""
    return getattr(settings, UPLOAD_HANDLER_SETTING, "") or ""
