from django import forms
from django.utils.translation import gettext_lazy as _


class BlockFormField(forms.CharField):
    """A form field that can render a StreamBlock value as a JSON string."""

    widget = forms.Textarea

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("help_text", _("Enter block data as JSON"))
        super().__init__(*args, **kwargs)


class ThemedFormMixin:
    """
    Mixin for Django forms that adds theme-aware styling context.

    Usage::

        class MyForm(ThemedFormMixin, forms.Form): ...


        # In a view:
        form = MyForm(theme=current_theme)
    """

    def __init__(self, *args, **kwargs):
        self.theme = kwargs.pop("theme", None)
        super().__init__(*args, **kwargs)

    def get_theme_context(self):
        if not self.theme:
            return {}
        return {
            "theme": self.theme,
            "theme_name": getattr(self.theme, "name", ""),
        }


class ThemedModelFormMixin(ThemedFormMixin):
    """
    Mixin for Django ModelForms that adds theme-aware styling context.
    """

    pass
