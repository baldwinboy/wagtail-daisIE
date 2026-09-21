"""Project account adapter.

The DaisyUI mixin comes first so DaisyUI email templates are used for allauth
emails, while any other adapter behaviour can still be overridden here.
"""

from allauth.account.adapter import DefaultAccountAdapter

from wagtail_daisIE.notifications.allauth import DaisyUIAccountAdapterMixin


class AccountAdapter(DaisyUIAccountAdapterMixin, DefaultAccountAdapter):
    """Use the DaisyUI allauth bridge and keep allauth's other behaviour."""
