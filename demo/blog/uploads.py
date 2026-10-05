"""Upload handler used by the demo's form field types.

Registered as ``handler`` in ``WAGTAIL_DAISIE_FORM_FIELD_TYPES``. A project
handler decides where the file goes and what reference is recorded in the
submission; here we persist to the default storage and return its URL.
"""

from pathlib import PurePosixPath

from django.core.files.storage import default_storage


def store_upload(*, page, form, field, file, request=None):
    """Save ``file`` to the default storage and return its public URL."""
    name = PurePosixPath(file.name).name
    stored = default_storage.save(f"form-uploads/{name}", file)
    return default_storage.url(stored)
