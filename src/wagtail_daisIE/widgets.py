import json
import re

from colorfield.widgets import ColorWidget
from django import forms
from django.db import models
from django.forms import ValidationError, widgets
from django.utils.translation import gettext_lazy as _
from wagtail import blocks

from wagtail_daisIE.choices.responsive import (
    RESPONSIVE_DESIGN_AREAS,
    RESPONSIVE_GROUPS_BY_KEY,
    RESPONSIVE_SIDES,
    RESPONSIVE_UTILITY_META,
)
from wagtail_daisIE.choices.utils import is_auto_utility


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
    def __init__(self, attrs=None, format="hex", alpha=True, force_alpha=True):
        self.format = format
        self.alpha = alpha
        self.force_alpha = force_alpha
        super().__init__(attrs)

    @property
    def media(self):
        # Coloris is loaded once globally (see wagtail_hooks); only the
        # colorfield initialiser is needed here. Including Coloris again via
        # ColorWidget's media would load it twice and create duplicate pickers.
        return forms.Media(js=["colorfield/colorfield.js"])

    def get_context(self, name, value, attrs=None):
        context = super().get_context(name, value, attrs)
        options = context.get("data_coloris_options", {})
        options["format"] = self.format
        options["alpha"] = self.alpha
        options["forceAlpha"] = self.force_alpha
        context["data_coloris_options"] = options
        return context


class DaisyUIThemeColorWidget(ColorWidget):
    """
    Same as DaisyUIColorWidget but allows pre-defined swatches and an explicit
    alpha policy.
    """

    def __init__(
        self,
        swatches=None,
        attrs=None,
        format="hex",
        alpha=True,
        force_alpha=True,
    ):
        self.swatches = swatches or []
        self.format = format
        self.alpha = alpha
        self.force_alpha = force_alpha
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
        options["format"] = self.format
        options["alpha"] = self.alpha
        options["forceAlpha"] = self.force_alpha
        context["data_coloris_options"] = options
        return context


# ---------------------------------------------------------------------------
# StreamBlock settings widgets
# ---------------------------------------------------------------------------


class DaisyUISwatchWidget(widgets.RadioSelect):
    """RadioSelect that renders each option as a colour-swatch tile."""

    template_name = "wagtail_daisIE/admin/daisyui_swatch_widget.html"

    def __init__(self, attrs=None, prefix=None, label=None):
        super().__init__(attrs=attrs)
        self.prefix = prefix or ""
        self.label = label or _("Swatches")

    @property
    def media(self):
        return forms.Media(js=["wagtail_daisIE/js/swatch_controller.js"])

    @property
    def color_map(self):
        """Colour map built on demand.

        Deliberately not computed in ``__init__``: widgets are instantiated at
        import time in block class bodies, and querying the database there
        triggers Django's "database during app initialization" warning.
        """
        return self._build_color_map()

    # Value policy hooks (overridden by ``DaisyUIRawSwatchWidget``).
    # ``get_context`` defines the algorithm once; subclasses only change how
    # values are represented.
    def normalise_value(self, value, color_map):
        return value

    def is_custom(self, value, color_map):
        marker = f"{self.prefix}-[#"
        return bool(value and value.startswith(marker) and value.endswith("]"))

    def custom_hex(self, value):
        marker = f"{self.prefix}-[#"
        if value and value.startswith(marker) and value.endswith("]"):
            return f"#{value[len(marker) : -1]}"
        return ""

    def choice_tile(self, choice_value, color_map):
        """Return ``(value, color)`` for a choice, or ``None`` to omit it."""
        return choice_value, color_map.get(choice_value, "#cccccc")

    def widget_extras(self, widget_ctx, value):
        """Hook for subclass-specific template context."""

    def get_context(self, name, value, attrs=None):
        from .utils import get_draftail_color_palette

        context = super().get_context(name, value, attrs)
        palette = get_draftail_color_palette()
        color_map = self._build_color_map(palette)
        normalised = self.normalise_value(value, color_map)
        is_custom = self.is_custom(normalised, color_map)
        custom_hex = self.custom_hex(normalised) if is_custom else ""

        tiles = []
        for choice_value, choice_label in self.choices:
            choice = self.choice_tile(choice_value, color_map)
            if choice is None:
                continue
            tile_value, tile_color = choice
            tiles.append(
                {
                    "value": tile_value,
                    "label": choice_label,
                    "color": tile_color,
                    "selected": not is_custom and tile_value == normalised,
                }
            )

        tiles.append(
            {
                "value": normalised if is_custom else "",
                "label": _("Custom"),
                "color": custom_hex,
                "selected": is_custom,
                "is_custom": True,
            }
        )

        widget_ctx = context["widget"]
        widget_ctx["tiles"] = tiles
        widget_ctx["is_custom"] = is_custom
        widget_ctx["custom_color"] = custom_hex
        widget_ctx["prefix"] = self.prefix
        widget_ctx["label"] = self.label
        self.widget_extras(widget_ctx, normalised)

        swatches = [entry["value"] for entry in palette if entry["value"]]
        widget_id = widget_ctx["attrs"].get("id") or ""
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
            # clicked; swatch_controller.js switches it inline for that widget.
            "inline": False,
        }
        widget_ctx["coloris_options_json"] = json.dumps(coloris_options)
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
            color_map[f"decoration-{key}"] = entry["value"]
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

    def normalise_value(self, value, color_map):
        # Accept legacy class-name values ("bg-primary") too, so existing
        # content keeps rendering correctly.
        return color_map.get(value, value)

    def is_custom(self, value, color_map):
        palette_hexes = set(color_map.values())
        return (
            bool(value)
            and isinstance(value, str)
            and value.startswith("#")
            and value not in palette_hexes
        )

    def custom_hex(self, value):
        return value or ""

    def choice_tile(self, choice_value, color_map):
        hex_value = color_map.get(choice_value)
        if hex_value is None:
            return None
        # The radio's submitted value is the hex, not the class.
        return hex_value, hex_value

    def widget_extras(self, widget_ctx, value):
        # The class-name prefix used to build ``bg-[#…]`` values does not
        # apply here — the raw widget stores hex directly.
        widget_ctx["prefix"] = ""
        widget_ctx["is_raw"] = True

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
        selected_label = ""
        for _i, (choice_value, choice_label) in enumerate(self.choices):
            is_selected = choice_value == value or (
                value == "auto" and is_auto_utility(choice_value)
            )
            if is_selected:
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
        context["widget"]["semantic_options"] = [
            option
            for group in context["widget"]["opt_groups"]
            if group["label"] != _("Preset sizes")
            for option in group["options"]
        ]
        context["widget"]["range_aria_label"] = (
            attrs.get("aria_label") if attrs and attrs.get("aria_label") else _("Value")
        )
        # The range slider covers every option; semantic buttons are quick
        # access shortcuts for the standalone/responsive values.
        selected_index = 0
        for i, option in enumerate(options):
            if option["selected"]:
                selected_index = i
                break
        context["widget"]["slider_max"] = max(0, len(options) - 1)
        context["widget"]["slider_index"] = selected_index
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
            if choice_value == "" or is_auto_utility(choice_value):
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

    @property
    def media(self):
        return forms.Media(js=["wagtail_daisIE/js/preset_slider_controller.js"])


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
        return context

    @property
    def media(self):
        return forms.Media(js=["wagtail_daisIE/js/number_slider_controller.js"])


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


class DaisyUIResponsiveUtilityWidget(widgets.Select):
    """Four-step responsive editor: area -> property -> side -> value.

    The native value ``<select>`` remains the submitted field and the no-JS
    fallback. All options are rendered server-side with ``data-*`` metadata;
    the editor controller filters them and ``w-zone`` switches the value
    control.
    """

    template_name = "wagtail_daisIE/admin/daisyui_responsive_utility_widget.html"

    @property
    def media(self):
        return forms.Media(
            js=[
                "wagtail_daisIE/js/preset_slider_controller.js",
                "wagtail_daisIE/js/responsive_utility_controller.js",
            ]
        )

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        """Keep the filter metadata on the option.

        Django's ``Select`` sets ``option_inherits_attrs = False`` and discards
        the ``attrs`` passed to ``create_option``, so merge them back into the
        rendered option here.
        """
        option = super().create_option(name, value, label, selected, index, subindex)
        if attrs:
            option["attrs"].update(attrs)
        return option

    def optgroups(self, name, value, attrs=None):
        """Render every option with the metadata the editor filters on."""
        if isinstance(value, (list, tuple)):
            value = value[0] if value else ""

        selected_value = value or ""
        current_meta = RESPONSIVE_UTILITY_META.get(
            selected_value,
            ("spacing", "padding", "all"),
        )
        groups = []

        for index, ((area_key, property_key, side_key), (label, options)) in enumerate(
            RESPONSIVE_GROUPS_BY_KEY.items()
        ):
            group_options = []
            for option_index, (option_value, option_label) in enumerate(options):
                # Only the current group's empty option is the selected "None".
                selected = option_value == selected_value and (
                    option_value != ""
                    or (area_key, property_key, side_key) == current_meta
                )
                group_options.append(
                    self.create_option(
                        name,
                        option_value,
                        option_label,
                        selected,
                        option_index,
                        attrs={
                            "data-area": area_key,
                            "data-property": property_key,
                            "data-side": side_key,
                        },
                    )
                )
            groups.append((label, group_options, index))

        return groups

    def get_context(self, name, value, attrs=None):
        context = super().get_context(name, value, attrs)
        widget_ctx = context["widget"]
        area_key, property_key, side_key = RESPONSIVE_UTILITY_META.get(
            value, ("spacing", "padding", "all")
        )

        areas = [
            {"key": area["key"], "label": area["label"]}
            for area in RESPONSIVE_DESIGN_AREAS
        ]
        properties = []
        current_property = None
        for area in RESPONSIVE_DESIGN_AREAS:
            for prop in area["properties"]:
                item = {
                    "key": prop["key"],
                    "label": prop["label"],
                    "area": area["key"],
                    "has_sides": prop["has_sides"],
                    "widget": prop["widget"],
                    "sides": ",".join(
                        side_key for side_key, _label, _choices in prop["sides"]
                    ),
                }
                properties.append(item)
                if area["key"] == area_key and prop["key"] == property_key:
                    current_property = item

        property_field_name = f"{name}-property"
        widget_ctx["areas"] = areas
        widget_ctx["properties"] = properties
        widget_ctx["property_field_name"] = property_field_name
        widget_ctx["sides"] = [
            {"key": key, "label": label} for key, label in RESPONSIVE_SIDES
        ]
        widget_ctx["side_rules_json"] = json.dumps(
            {property_field_name: ["padding", "margin", "gap"]}
        )
        widget_ctx["current_area"] = area_key
        widget_ctx["current_property"] = property_key
        widget_ctx["current_side"] = side_key
        widget_ctx["current_value"] = value or ""
        widget_ctx["current_widget"] = (
            current_property["widget"] if current_property else "slider"
        )
        widget_ctx["current_has_sides"] = (
            current_property["has_sides"] if current_property else True
        )

        widget_ctx["semantic_options"] = []
        widget_ctx["range_aria_label"] = _("Value")

        _group_label, options = RESPONSIVE_GROUPS_BY_KEY.get(
            (area_key, property_key, side_key),
            ("", []),
        )
        selected_index = 0
        selected_label = options[0][1] if options else ""
        for index, (option_value, option_label) in enumerate(options):
            if option_value == value:
                selected_index = index
                selected_label = option_label
                break
        widget_ctx["slider_max"] = max(0, len(options) - 1)
        widget_ctx["slider_index"] = selected_index
        widget_ctx["selected_label"] = selected_label
        return context


class DaisieAutocompleteSelectMultiple(forms.SelectMultiple):
    """A ``SelectMultiple`` enhanced into a searchable token control.

    The native ``<select multiple>`` is always rendered (and stays usable with
    JavaScript disabled); ``daisyui_autocomplete.js`` hides it and reveals the
    token UI. The widget ships its own JS through ``Media`` so it works on
    standalone form pages (which only render ``{{ form.media }}``) and in the
    admin alike.
    """

    template_name = "wagtail_daisIE/admin/daisyui_autocomplete_widget.html"
    allow_multiple_selected = True

    def __init__(self, attrs=None, choices=(), pattern="", placeholder=""):
        super().__init__(attrs)
        if choices:
            self.choices = choices
        self.pattern = pattern
        self.placeholder = placeholder

    @property
    def media(self):
        return forms.Media(js=["wagtail_daisIE/js/daisyui_autocomplete.js"])

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        options = []
        for _group_name, group_options, _index in context["widget"]["optgroups"]:
            for option in group_options:
                options.append(
                    {
                        "value": option["value"],
                        "label": option["label"],
                        "selected": option["selected"] or False,
                    }
                )
        context["autocomplete_options"] = options
        context["autocomplete_placeholder"] = self.placeholder or ""
        context["autocomplete_pattern"] = self.pattern or ""
        return context


class LayerTypeSelect(forms.Select):
    """``layer_type`` select wired to the background-layer Stimulus controller.

    The controller (``daisie-background-layer``) reads this element and toggles
    the ``.layer-*`` field groups on change. Shared by StreamField blocks and
    the theme's inline background-layer panel.
    """

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["data-controller"] = "daisie-background-layer"
        return attrs
