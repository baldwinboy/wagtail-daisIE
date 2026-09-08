import json
import re

from colorfield.widgets import ColorWidget
from django import forms
from django.db import models
from django.forms import ValidationError, widgets
from django.utils.translation import gettext_lazy as _
from wagtail import blocks


class DaisyUISizeUnitChoices(models.TextChoices):
    PX = "px", _("px (Pixels)")
    EM = "em", _("em (Parent element's font size)")
    REM = "rem", _("rem (Root element's font size)")
    VW = "vw", _("vw (Viewport width)")
    VH = "vh", _("vh (Viewport height)")
    PT = "pt", _("pt (Points)")
    PC = "pc", _("pc (Picas)")
    IN = "in", _("in (Inches)")
    CM = "cm", _("cm (Centimeters)")
    MM = "mm", _("mm (Millimeters)")
    Q = "q", _("q (Quarters)")


class DaisyUISize:
    def __init__(self, value: float, unit: str):
        self.value = value
        self.unit = unit

    def __str__(self):
        return f"{self.value}{self.unit}"

    def __repr__(self):
        return f"DaisyUISize({self.value!r}, {self.unit!r})"

    def __len__(self):
        return len(str(self))

    def __eq__(self, other):
        if isinstance(other, DaisyUISize):
            return self.value == other.value and self.unit == other.unit
        return NotImplemented

    @classmethod
    def from_value(cls, value):
        if isinstance(value, DaisyUISize) or value is None:
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None

            # optional whitespace, and a unit (letters)
            match = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*([a-zA-Z]+)", value)
            if not match:
                raise ValidationError(
                    _(
                        'Invalid CSS size format. Expected a number followed by a unit, e.g. "10px".'
                    ),
                    code="wagtail_daisIE.invalid_size_format",
                )

            value, unit = match.groups()

            if unit not in DaisyUISizeUnitChoices.values:
                raise ValidationError(
                    _("Invalid CSS size unit. Expected one of: %(choices)s"),
                    code="wagtail_daisIE.invalid_size_unit",
                    params={"choices": ", ".join(DaisyUISizeUnitChoices.values)},
                )

            try:
                value = float(value)
            except ValueError as exc:
                raise ValidationError(
                    _(
                        'Invalid CSS size value. Expected a number followed by a unit, e.g. "10px".'
                    ),
                    code="wagtail_daisIE.invalid_size_value",
                ) from exc

            return DaisyUISize(float(value), unit)


class DaisyUISizeWidget(forms.MultiWidget):
    template_name = "wagtail_daisIE/admin/daisyui_size_widget.html"

    def __init__(self, attrs=None):
        _widgets = (
            widgets.NumberInput(attrs={"step": "any", "placeholder": "Value"}),
            widgets.Select(choices=DaisyUISizeUnitChoices.choices),
        )
        super().__init__(_widgets, attrs)

    def decompress(self, value):
        """
        Convert a single DaisyUISize value into a list [number, unit]
        for the two sub-widgets.
        """
        if value is None:
            return [None, None]
        if isinstance(value, DaisyUISize):
            return [value.value, value.unit]
        if isinstance(value, str):
            obj = DaisyUISize.from_value(value)
            if obj:
                return [obj.value, obj.unit]
        return [None, None]


class DaisyUIColorWidget(ColorWidget):
    @property
    def media(self):
        # Coloris is loaded once globally (see wagtail_hooks); only the
        # colorfield initialiser is needed here. Including Coloris again via
        # ColorWidget's media would load it twice and create duplicate pickers.
        return forms.Media(js=["colorfield/colorfield.js"])

    def get_context(self, name, value, attrs=None):
        context = super().get_context(name, value, attrs)
        options = context.get("data_coloris_options", {})
        options["format"] = "hexa"
        options["alpha"] = True
        options["forceAlpha"] = True
        context["data_coloris_options"] = options
        return context


class DaisyUIThemeColorWidget(ColorWidget):
    """
    Same as DaisyUIColorWidget but allows passing pre-defined swatches.
    """

    def __init__(self, swatches=None, attrs=None):
        self.swatches = swatches or []
        super().__init__(attrs)

    @property
    def media(self):
        return forms.Media(js=["colorfield/colorfield.js"])

    def get_context(self, name, value, attrs=None):
        context = super().get_context(name, value, attrs)
        # Merge swatches into the Coloris options
        options = context.get("data_coloris_options", {})
        options["swatches"] = self.swatches
        options["swatchesOnly"] = False  # allow picking any colour
        options["format"] = "hexa"
        options["alpha"] = True
        options["forceAlpha"] = True
        context["data_coloris_options"] = options
        return context


# ---------------------------------------------------------------------------
# StreamBlock settings widgets
# ---------------------------------------------------------------------------


class DaisyUISwatchWidget(widgets.RadioSelect):
    """RadioSelect that renders each option as a colour-swatch tile."""

    template_name = "wagtail_daisIE/admin/daisyui_swatch_widget.html"

    def __init__(self, attrs=None, prefix=None):
        super().__init__(attrs=attrs)
        self.prefix = prefix or ""

    @property
    def color_map(self):
        """Colour map built on demand.

        Deliberately not computed in ``__init__``: widgets are instantiated at
        import time in block class bodies, and querying the database there
        triggers Django's "database during app initialization" warning.
        """
        return self._build_color_map()

    def get_context(self, name, value, attrs=None):
        from .utils import get_draftail_color_palette

        context = super().get_context(name, value, attrs)
        palette = get_draftail_color_palette()
        color_map = self._build_color_map(palette)
        marker = f"{self.prefix}-[#"
        is_custom = bool(value and value.startswith(marker) and value.endswith("]"))
        custom_hex = f"#{value[len(marker) : -1]}" if is_custom else ""

        tiles = []
        for choice_value, choice_label in self.choices:
            tiles.append(
                {
                    "value": choice_value,
                    "label": choice_label,
                    "color": color_map.get(choice_value, "#cccccc"),
                    "selected": not is_custom and choice_value == value,
                }
            )

        tiles.append(
            {
                "value": value if is_custom else "",
                "label": _("Custom"),
                "color": custom_hex,
                "selected": is_custom,
                "is_custom": True,
            }
        )

        context["widget"]["tiles"] = tiles
        context["widget"]["is_custom"] = is_custom
        context["widget"]["custom_color"] = custom_hex
        context["widget"]["prefix"] = self.prefix

        swatches = [entry["value"] for entry in palette if entry["value"]]
        widget_id = context["widget"]["attrs"].get("id") or ""
        coloris_options = {
            # Scope the picker to this specific widget instance. In the
            # telepath payload the id is the "__ID__" token, which is
            # rewritten to the real id when the widget is rendered.
            "parent": f"#{widget_id}" if widget_id else ".daisyui-swatch-widget",
            "swatches": swatches,
            "swatchesOnly": False,
            "format": "hex",
            "alpha": False,
            # Coloris is kept in popover mode until the "Custom" tile is
            # clicked; block_settings.js switches it inline for that widget.
            "inline": False,
        }
        context["widget"]["coloris_options_json"] = json.dumps(coloris_options)
        return context

    def _build_color_map(self, palette=None):
        if palette is None:
            from .utils import get_draftail_color_palette

            palette = get_draftail_color_palette()

        color_map = {}
        for entry in palette:
            key = entry["key"].replace("_", "-")
            color_map[f"bg-{key}"] = entry["value"]
            color_map[f"text-{key}"] = entry["value"]
            color_map[f"border-{key}"] = entry["value"]
        return color_map


class DaisyUIRawSwatchWidget(DaisyUISwatchWidget):
    """
    Like :class:`DaisyUISwatchWidget`, but the submitted/stored value is the
    raw CSS colour (e.g. ``"#422ad5ff"``) rather than the DaisyUI utility
    class name (e.g. ``"bg-primary"``).

    Example::

        bg_color = blocks.ChoiceBlock(
            choices=DAISYUI_BG_COLOR_CHOICES,
            widget=DaisyUIRawSwatchWidget(prefix="bg"),
        )

    Selecting the "Primary" swatch stores ``"#422ad5ff"`` on the block.
    """

    def get_context(self, name, value, attrs=None):
        # Accept legacy class-name values ("bg-primary") too, so existing
        # content keeps rendering correctly.
        color_map = self._build_color_map()
        normalised = color_map.get(value, value)

        context = super().get_context(name, normalised, attrs)
        widget_ctx = context["widget"]

        palette_hexes = set(color_map.values())
        is_custom = (
            bool(normalised)
            and isinstance(normalised, str)
            and normalised.startswith("#")
            and normalised not in palette_hexes
        )

        tiles = []
        for choice_value, choice_label in self.choices:
            hex_value = color_map.get(choice_value)
            if hex_value is None:
                continue
            tiles.append(
                {
                    # The radio's submitted value is the hex, not the class.
                    "value": hex_value,
                    "label": choice_label,
                    "color": hex_value,
                    "selected": not is_custom and normalised == hex_value,
                }
            )

        tiles.append(
            {
                "value": normalised if is_custom else "",
                "label": _("Custom"),
                "color": normalised if is_custom else "",
                "selected": is_custom,
                "is_custom": True,
                "is_raw": True,
            }
        )

        widget_ctx["tiles"] = tiles
        widget_ctx["is_custom"] = is_custom
        widget_ctx["custom_color"] = normalised if is_custom else ""
        # The class-name prefix used to build ``bg-[#…]`` values does not
        # apply here — the raw widget stores hex directly.
        widget_ctx["prefix"] = ""
        widget_ctx["is_raw"] = True

        return context

    def value_from_datadict(self, data, files, name):
        value = super().value_from_datadict(data, files, name)
        if not value:
            return value
        color_map = self._build_color_map()
        # Palette class name -> raw hex.
        if value in color_map:
            return color_map[value]
        # Prefixed arbitrary value ``bg-[#abcdef]`` -> raw hex (defensive).
        marker = f"{self.prefix}-[#"
        if value.startswith(marker) and value.endswith("]"):
            return f"#{value[len(marker) : -1]}"
        return value


class DaisyUISliderWidget(widgets.Select):
    """Select that renders a <select> (value carrier) + a range slider (visual).

    Options are split into sections so the long size/spacing choice lists stay
    navigable: the ``None`` and ``auto`` values form a "None / Auto" section and
    the rest is split between "Preset sizes" (fixed numeric units) and
    "Responsive sizes" (viewport/element-relative suffixes such as ``full`` or
    ``svw``).
    """

    template_name = "wagtail_daisIE/admin/daisyui_slider_widget.html"

    # Tailwind suffixes that map to viewport/element-relative sizes rather
    # than fixed numeric units. Used to section the option list.
    RESPONSIVE_SIZE_SUFFIXES = frozenset(
        {
            "full",
            "min",
            "max",
            "fit",
            "screen",
            "dvw",
            "dvh",
            "lvw",
            "lvh",
            "svw",
            "svh",
        }
    )

    def get_context(self, name, value, attrs=None):
        context = super().get_context(name, value, attrs)
        options = []
        index = 0
        selected_label = ""
        for i, (choice_value, choice_label) in enumerate(self.choices):
            is_selected = choice_value == value
            if is_selected:
                index = i
                selected_label = choice_label
            options.append(
                {
                    "value": choice_value,
                    "label": choice_label,
                    "selected": is_selected,
                }
            )
        context["widget"]["options"] = options
        context["widget"]["opt_groups"] = self._build_opt_groups(options)
        context["widget"]["slider_max"] = max(0, len(options) - 1)
        context["widget"]["slider_index"] = index
        context["widget"]["selected_label"] = selected_label
        return context

    def _build_opt_groups(self, options):
        """Split the flat options into optgroups.

        ``None`` and ``auto`` form the first group; the rest is split between
        ``Preset sizes`` (fixed numeric units) and ``Responsive sizes``.
        """
        standalone = []
        preset = []
        responsive = []
        for option in options:
            choice_value = option["value"]
            if choice_value == "" or choice_value == "auto":
                standalone.append(option)
            else:
                suffix = choice_value.split("-")[-1]
                bucket = (
                    responsive if suffix in self.RESPONSIVE_SIZE_SUFFIXES else preset
                )
                bucket.append(option)

        groups = []
        if standalone:
            groups.append({"label": _("None / Auto"), "options": standalone})
        if preset:
            groups.append({"label": _("Preset sizes"), "options": preset})
        if responsive:
            groups.append({"label": _("Responsive sizes"), "options": responsive})
        return groups


class DaisyUINumberSliderWidget(widgets.NumberInput):
    """Numeric slider: a range input (visual) + a number input (value carrier).

    Intended for ``IntegerBlock`` fields with a bounded range, e.g.
    ``border_width``. The number input is the submitted value carrier; an empty
    value means "no value" (None). ``suffix`` (e.g. ``"px"``, ``"deg"``) is
    shown next to the readout for display only.
    """

    template_name = "wagtail_daisIE/admin/daisyui_number_slider_widget.html"

    def __init__(
        self,
        attrs=None,
        min_value=0,
        max_value=100,
        step=1,
        suffix="",
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.suffix = suffix
        super().__init__(attrs)

    def get_context(self, name, value, attrs=None):
        context = super().get_context(name, value, attrs)
        widget_ctx = context["widget"]
        # NumberInput.format_value keeps None; hardcode it to "" so the
        # number input renders as empty rather than "None".
        widget_ctx["value"] = "" if widget_ctx["value"] is None else widget_ctx["value"]
        try:
            current = int(float(value))
        except (TypeError, ValueError):
            current = self.min_value
        current = min(max(current, self.min_value), self.max_value)
        widget_ctx["min"] = self.min_value
        widget_ctx["max"] = self.max_value
        widget_ctx["step"] = self.step
        widget_ctx["suffix"] = self.suffix
        widget_ctx["current"] = current
        widget_ctx["label"] = (
            _("None") if value in (None, "") else f"{current}{self.suffix}"
        )
        return context


class DaisyUIIntegerBlock(blocks.IntegerBlock):
    """IntegerBlock that actually applies the ``widget`` kwarg to its field.

    Wagtail's ``IntegerBlock`` swallows ``widget`` into the block meta instead
    of passing it to the underlying ``forms.IntegerField`` (unlike
    ``ChoiceBlock``), so numeric widgets such as
    :class:`DaisyUINumberSliderWidget` would otherwise be silently ignored.
    """

    def __init__(
        self,
        required=True,
        help_text=None,
        min_value=None,
        max_value=None,
        validators=(),
        widget=None,
        **kwargs,
    ):
        super().__init__(
            required=required,
            help_text=help_text,
            min_value=min_value,
            max_value=max_value,
            validators=validators,
            widget=widget,
            **kwargs,
        )
        if widget is not None:
            self.field.widget = widget

    def deconstruct(self):
        """Deconstruct as a plain ``IntegerBlock`` without the widget.

        Widgets provide no migration serialization method, so the numeric
        widget is dropped from the frozen definition (mirroring
        ``ChoiceBlock``).
        """
        _path, args, kwargs = super().deconstruct()
        kwargs = {key: value for key, value in kwargs.items() if key != "widget"}
        return ("wagtail.blocks.IntegerBlock", args, kwargs)


class DaisyUIAlignWidget(widgets.RadioSelect):
    """RadioSelect that renders each option as an alignment icon tile."""

    template_name = "wagtail_daisIE/admin/daisyui_align_widget.html"

    ALIGN_ICONS = {
        "": "—",
        "text-left": "<<<",
        "text-center": "===",
        "text-right": ">>>",
        "text-justify": "<=>",
    }

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs)

    def get_context(self, name, value, attrs=None):
        context = super().get_context(name, value, attrs)
        tiles = []
        for choice_value, choice_label in self.choices:
            tiles.append(
                {
                    "value": choice_value,
                    "label": choice_label,
                    "icon": self.ALIGN_ICONS.get(choice_value, ""),
                    "selected": choice_value == value,
                }
            )
        context["widget"]["tiles"] = tiles
        return context
