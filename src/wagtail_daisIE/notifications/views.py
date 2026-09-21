"""Public subscribe endpoint for newsletter blocks."""

from __future__ import annotations

from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import SubscribeForm
from .models import AudienceMember


RATE_LIMIT_SECONDS = 60


def _wants_json(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return True
    return "application/json" in request.headers.get("accept", "")


def _client_ip(request):
    return request.META.get("REMOTE_ADDR", "")


def _redirect_back(request, *, subscribed=False):
    url = request.META.get("HTTP_REFERER") or "/"
    if subscribed:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}subscribed=1"
    return redirect(url)


@require_POST
def subscribe(request):
    """Add an email address to a manual audience."""
    if not cache.add(
        f"wagtail_daisIE:subscribe:{_client_ip(request)}",
        True,
        timeout=RATE_LIMIT_SECONDS,
    ):
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": "rate_limited"}, status=429)
        messages.error(request, _("Please wait a moment and try again."))
        return _redirect_back(request)

    form = SubscribeForm(request.POST)
    if not form.is_valid():
        if _wants_json(request):
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        messages.error(request, _("Please enter a valid email address."))
        return _redirect_back(request)

    audience = form.cleaned_data["audience"]
    email = form.cleaned_data["email"].strip().lower()
    member, created = AudienceMember.objects.get_or_create(
        audience=audience,
        email=email,
        defaults={
            "name": form.cleaned_data.get("name", ""),
            "is_active": True,
        },
    )
    if not created and not member.is_active:
        member.is_active = True
        member.save(update_fields=["is_active"])

    if _wants_json(request):
        return JsonResponse({"ok": True, "created": created})

    messages.success(request, _("Thanks! You are subscribed."))
    return _redirect_back(request, subscribed=True)
