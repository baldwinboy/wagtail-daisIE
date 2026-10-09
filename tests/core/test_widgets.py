import importlib
import json
import sys

import pytest

from django.db import connection
from django.test.utils import CaptureQueriesContext
from wagtail.admin.telepath import JSContext

from wagtail_daisIE.blocks.base import BorderBlock
from wagtail_daisIE.blocks.inline import InlineTextBlock
from wagtail_daisIE.models import DaisyUITheme
from wagtail_daisIE.pages import get_default_theme_id
from wagtail_daisIE.widgets import (
    DaisieAutocompleteSelectMultiple,
    DaisyUIAlignWidget,
    DaisyUIIntegerBlock,
    DaisyUINumberSliderWidget,
    DaisyUIRawSwatchWidget,
    DaisyUISliderWidget,
    DaisyUISwatchWidget,
)


@pytest.mark.django_db
class TestDaisyUISwatchWidget:
    def test_custom_value_and_color_map(self):
        widget = DaisyUISwatchWidget(prefix="bg")
        widget.choices = [("", "None"), ("bg-primary", "Primary")]
        html = widget.render("bg_color", "bg-[#ff0000]", attrs={"id": "__ID__"})
        assert 'value="bg-[#ff0000]"' in html
        assert "daisyui-swatch-radio--custom" in html
        assert 'data-prefix="bg"' in html and 'value="#ff0000"' in html

        color_map = widget.color_map
        for name in ("primary", "secondary", "accent", "neutral", "info", "success"):
            # The content colour must be distinct from the base colour.
            assert f"bg-{name}-content" in color_map
            assert color_map[f"bg-{name}-content"] not in (
                "#cccccc",
                color_map[f"bg-{name}"],
            )


class TestWidgetRendering:
    def test_raw_swatch_and_sliders(self):
        raw = DaisyUIRawSwatchWidget(prefix="bg")
        raw.choices = [("", "None"), ("bg-primary", "Primary")]
        assert (
            raw.value_from_datadict({"bg_color": "bg-primary"}, None, "bg_color")
            == raw.color_map["bg-primary"]
        )
        assert (
            raw.value_from_datadict({"bg_color": "#1e0000"}, None, "bg_color")
            == "#1e0000"
        )

        slider = DaisyUISliderWidget()
        slider.choices = [("", "None"), ("auto", "Auto"), ("m-4", "4")]
        html = slider.render("__NAME__", "auto", attrs={"id": "__ID__"})
        assert 'value="auto"' in html
        assert "None / Auto" in html and 'optgroup label="Preset sizes"' in html

        responsive = DaisyUISliderWidget()
        responsive.choices = [
            ("", "None"),
            ("p-4", "4"),
            ("w-full", "Full"),
            ("h-svw", "Smallest visible width"),
        ]
        html = responsive.render("__NAME__", "p-4", attrs={"id": "__ID__"})
        assert "Preset sizes" in html and "Responsive sizes" in html
        assert 'value="w-full"' in html and 'value="h-svw"' in html

        number = DaisyUINumberSliderWidget(min_value=0, max_value=10, step=1)
        assert 'value="10"' in number.render("__NAME__", 50, attrs={"id": "__ID__"})

        autocomplete = DaisieAutocompleteSelectMultiple(
            choices=[("a", "Alpha"), ("b", "Bravo")], placeholder="Pick"
        )
        html = autocomplete.render("tags", ["a"], attrs={"id": "__ID__"})
        assert 'name="tags"' in html
        assert "data-daisyui-autocomplete" in html
        assert 'value="a" selected' in html
        assert "Alpha" in html and "Bravo" in html
        assert "daisyui_autocomplete.js" in str(autocomplete.media)


class TestBlockWidgets:
    def test_design_and_numeric_widgets(self):
        typography = InlineTextBlock().child_blocks["design"].child_blocks["typography"]
        mapping = {
            "text_color": DaisyUISwatchWidget,
            "font_size": DaisyUISliderWidget,
            "font_weight": DaisyUISliderWidget,
            "text_align": DaisyUIAlignWidget,
            "line_height": DaisyUISliderWidget,
            "letter_spacing": DaisyUISliderWidget,
        }
        for name, widget_class in mapping.items():
            assert isinstance(typography.child_blocks[name].field.widget, widget_class)

        from wagtail_daisIE.base_blocks.background_layer import (
            BackgroundLayerBlock,
            GradientStopBlock,
        )
        from wagtail_daisIE.blocks.layout import GridBlock

        for block, field_name in [
            (BorderBlock(), "border_width"),
            (GridBlock(), "num_columns"),
            (GradientStopBlock(), "position"),
            (BackgroundLayerBlock(), "gradient_angle"),
        ]:
            child = block.child_blocks[field_name]
            assert isinstance(child, DaisyUIIntegerBlock)
            assert isinstance(child.field.widget, DaisyUINumberSliderWidget)


@pytest.mark.django_db
class TestNoImportTimeQueries:
    def test_no_queries_at_init_or_import(self):
        with CaptureQueriesContext(connection) as ctx:
            DaisyUISwatchWidget(prefix="bg")
            DaisyUIRawSwatchWidget(prefix="bg")
            DaisieAutocompleteSelectMultiple(choices=[("a", "A")])
        assert len(ctx) == 0

        for name in list(sys.modules):
            if name.startswith("wagtail_daisIE.base_blocks"):
                del sys.modules[name]
        with CaptureQueriesContext(connection) as ctx:
            importlib.import_module("wagtail_daisIE.base_blocks.background_layer")
            importlib.import_module("wagtail_daisIE.base_blocks.fields")
        assert len(ctx) == 0

        # The query may happen on access, but never from ``__init__``.
        assert DaisyUISwatchWidget(prefix="bg").color_map["bg-primary"] != "#cccccc"


class TestStyledPageMixinLazyTheme:
    @pytest.mark.django_db
    def test_default_theme_id_is_resolved_lazily(self):
        theme = DaisyUITheme.objects.create(name="lazy-default", default=True)
        assert get_default_theme_id() == theme.pk


@pytest.mark.django_db
class TestWidgetAdapters:
    def test_widgets_pack_with_expected_constructors(self):
        payload = json.dumps(JSContext().pack(InlineTextBlock()))
        for adapter in (
            "wagtail_daisIE.widgets.SwatchSelect",
            "wagtail_daisIE.widgets.SliderSelect",
            "wagtail_daisIE.widgets.NumberSlider",
        ):
            assert adapter in payload, adapter

        from wagtail_daisIE.icons.blocks import IconChooserBlock

        # The icon chooser has no custom adapter: it packs through Wagtail's
        # generic widget adapter, with the picker driven by a Stimulus
        # controller shipped via the widget's media.
        icon_block = IconChooserBlock()
        icon_payload = json.dumps(JSContext().pack(icon_block))
        assert "wagtail.widgets.Widget" in icon_payload
        assert "wagtail_daisIE.widgets.IconChooser" not in icon_payload

        # A value-less telepath placeholder must not bake in ``"None"``.
        html = icon_block.field.widget.render("__NAME__", None, attrs={"id": "__ID__"})
        assert 'value="None"' not in html
        assert 'value=""' in html
