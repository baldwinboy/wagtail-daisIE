"""Detail-page configuration errors."""

from django.core.exceptions import ImproperlyConfigured


class DetailPageConfigurationError(ImproperlyConfigured):
    """Raised when a detail-page configuration cannot be resolved exactly."""


__all__ = ["DetailPageConfigurationError"]
