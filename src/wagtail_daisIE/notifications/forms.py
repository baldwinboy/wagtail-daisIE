"""Forms for the public subscribe endpoint."""

from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Audience


class SubscribeForm(forms.Form):
    audience = forms.ModelChoiceField(
        queryset=Audience.objects.none(),
        label=_("Audience"),
    )
    email = forms.EmailField(label=_("Email"))
    name = forms.CharField(max_length=255, required=False, label=_("Name"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["audience"].queryset = Audience.objects.filter(
            kind=Audience.Kind.MANUAL, is_active=True
        )
