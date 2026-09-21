"""Audience rules used by the demo.

These are declared in ``WAGTAIL_DAISIE_AUDIENCE_RULES`` and evaluated at render
time. ``staff_users`` is also used as the campaign ``queryset``.
"""

from django.contrib.auth import get_user_model

from wagtail_daisIE.notifications.models import AudienceMember


def is_staff(request):
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and user.is_staff)


def has_newsletter(request):
    if request is None:
        return False
    email = ""
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        email = user.email
    return bool(email) and AudienceMember.objects.filter(
        audience__name="Newsletter", email__iexact=email
    ).exists()


def staff_users():
    return get_user_model().objects.filter(is_staff=True)
