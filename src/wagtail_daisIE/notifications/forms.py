"""Forms for the public subscribe endpoint."""

from __future__ import annotations

from django import forms

from .models import Audience


class SubscribeForm(forms.Form):
    audience = forms.ModelChoiceField(
        queryset=Audience.objects.none(),
    )
    email = forms.EmailField()
    name = forms.CharField(max_length=255, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["audience"].queryset = Audience.objects.filter(
            kind=Audience.Kind.MANUAL, is_active=True
        )
