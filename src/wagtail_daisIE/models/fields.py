from colorfield.fields import ColorField
from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from wagtail_daisIE.form_fields import DaisyUISizeFormField
from wagtail_daisIE.validators import color_hex_or_hexa_validator
from wagtail_daisIE.widgets import DaisyUISize, DaisyUIThemeColorWidget


class DaisyUIColorSchemeChoices(models.TextChoices):
    NORMAL = "normal", _("Normal")
    LIGHT = "light", _("Light")
    DARK = "dark", _("Dark")


class DaisyUIColorField(ColorField):
    """Colour field that uses the package's Coloris widget.

    ``colorfield``'s ``ColorField.formfield`` always substitutes its own
    ``ColorWidget``, which loads Coloris again on top of the global admin
    script. Supplying our widget avoids a duplicate Coloris instance.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Accept both hex (#rrggbb) and hexa (#rrggbbaa) values, since the
        # Coloris picker may hand back either depending on how a colour was
        # picked or typed. ``validators`` is a cached_property that is already
        # populated by ``CharField.__init__``, so replace it wholesale rather
        # than only swapping ``default_validators``.
        self.default_validators = [color_hex_or_hexa_validator]
        self.validators = [
            color_hex_or_hexa_validator,
            MaxLengthValidator(self.max_length),
        ]

    def formfield(self, **kwargs):
        formfield = super().formfield(**kwargs)
        formfield.validators = [color_hex_or_hexa_validator]
        formfield.widget = DaisyUIThemeColorWidget()
        return formfield


class DaisyUISizeField(models.CharField):
    description = _("A CSS size (e.g. 10px, 2.5em)")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 20)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if kwargs.get("max_length") == 20:
            kwargs.pop("max_length", None)
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        """Convert the database string to a Python DaisyUISize object."""
        if value is None:
            return value
        return self.to_python(value)

    def to_python(self, value):
        return DaisyUISize.from_value(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if isinstance(value, DaisyUISize):
            return str(value)
        return value

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def formfield(self, **kwargs):
        defaults = {
            "form_class": DaisyUISizeFormField,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
