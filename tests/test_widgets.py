import html
import importlib
import sys

import pytest

from django.db import connection
from django.test.utils import CaptureQueriesContext
from wagtail.admin.telepath import JSContext

from wagtail_daisIE.blocks.base import BorderBlock
from wagtail_daisIE.blocks.cards import CardBlock
from wagtail_daisIE.blocks.inline import InlineTextBlock
from wagtail_daisIE.blocks.link import ButtonBlock
from wagtail_daisIE.blocks.section import SectionBlock
from wagtail_daisIE.models import DaisyUITheme
from wagtail_daisIE.pages import StyledPageMixin, get_default_theme_id
from wagtail_daisIE.widgets import (
    DaisyUIAlignWidget,
    DaisyUIIntegerBlock,
    DaisyUINumberSliderWidget,
    DaisyUIRawSwatchWidget,
    DaisyUISliderWidget,
    DaisyUISwatchWidget,
)


@pytest.mark.django_db
class TestDaisyUISwatchWidget:
    def _widget(self):
        widget = DaisyUISwatchWidget(prefix="bg")
        widget.choices = [("", "None"), ("bg-primary", "Primary")]
        return widget

    def test_renders_choices_as_tiles(self):
        widget = DaisyUISwatchWidget()
        widget.choices = [("", "None"), ("bg-primary", "Primary")]
        html = widget.render("__NAME__", "", attrs={"id": "__ID__"})
        assert 'name="__NAME__"' in html
        assert 'id="__ID__"' in html
        assert 'value="bg-primary"' in html
        assert "daisyui-swatch-tile" in html

    def test_custom_value_is_parsed_and_rendered(self):
        html = self._widget().render("bg_color", "bg-[#ff0000]", attrs={"id": "__ID__"})
        assert 'value="bg-[#ff0000]"' in html
        assert "daisyui-swatch-radio--custom" in html
        assert 'data-prefix="bg"' in html
        assert 'value="#ff0000"' in html

    def test_empty_value_still_renders_custom_radio(self):
        html = self._widget().render("bg_color", "", attrs={"id": "__ID__"})
        assert "daisyui-swatch-radio--custom" in html

    def test_coloris_options_are_deferred_and_widget_scoped(self):
        rendered = html.unescape(
            self._widget().render("bg_color", "", attrs={"id": "__ID__"})
        )
        assert '"parent": "#__ID__"' in rendered
        assert '"inline": false' in rendered
        assert 'data-daisyui-coloris-parent="__ID__"' in rendered

    def test_preset_value_is_not_treated_as_custom(self):
        html = self._widget().render("bg_color", "bg-primary", attrs={"id": "__ID__"})
        assert "daisyui-swatch-radio--custom" in html
        assert 'value="#ff0000"' not in html

    def test_color_map_includes_content_and_border_colors(self):
        widget = DaisyUISwatchWidget(prefix="bg")
        assert widget.color_map["bg-primary-content"] != "#cccccc"
        assert widget.color_map["text-primary-content"] != "#cccccc"
        assert widget.color_map["border-primary-content"] != "#cccccc"


class TestDaisyUIRawSwatchWidget:
    def _widget(self):
        widget = DaisyUIRawSwatchWidget(prefix="bg")
        widget.choices = [("", "None"), ("bg-primary", "Primary")]
        return widget

    def test_custom_tile_is_marked_raw(self):
        html = self._widget().render("bg_color", "#1234ab", attrs={"id": "__ID__"})
        assert 'value="#1234ab"' in html
        assert 'data-raw="true"' in html
        assert 'data-prefix=""' in html
        assert "daisyui-swatch-radio--custom" in html

    def test_preset_value_normalised_to_hex(self):
        widget = self._widget()
        html = widget.render("bg_color", "bg-primary", attrs={"id": "__ID__"})
        assert f'value="{widget.color_map["bg-primary"]}"' in html
        assert not widget.color_map["bg-primary"].startswith("bg-")

    def test_value_from_datadict_maps_palette_and_passes_hex(self):
        widget = self._widget()
        assert (
            widget.value_from_datadict({"bg_color": "bg-primary"}, None, "bg_color")
            == widget.color_map["bg-primary"]
        )
        assert (
            widget.value_from_datadict({"bg_color": "#1e0000"}, None, "bg_color")
            == "#1e0000"
        )


class TestDaisyUISliderWidget:
    def test_renders_select_and_range_with_choices(self):
        widget = DaisyUISliderWidget()
        widget.choices = [
            ("", "None"),
            ("p-2", "2"),
            ("p-4", "4"),
        ]
        html = widget.render("__NAME__", "p-4", attrs={"id": "__ID__"})
        assert 'name="__NAME__"' in html
        assert 'id="__ID__"' in html
        assert 'value="p-4"' in html
        assert 'value="p-2"' in html
        assert "daisyui-slider-range" in html
        assert 'max="2"' in html

    def test_selected_option_marked(self):
        widget = DaisyUISliderWidget()
        widget.choices = [("", "None"), ("p-4", "4")]
        html = widget.render("__NAME__", "p-4", attrs={"id": "__ID__"})
        assert html.count("selected") == 1

    def test_auto_option_is_grouped_as_standalone(self):
        widget = DaisyUISliderWidget()
        widget.choices = [("", "None"), ("auto", "Auto"), ("m-4", "4")]
        html = widget.render("__NAME__", "auto", attrs={"id": "__ID__"})
        assert 'value="auto"' in html
        assert "None / Auto" in html
        assert 'optgroup label="Preset sizes"' in html

    def test_responsive_suffixes_are_grouped(self):
        widget = DaisyUISliderWidget()
        widget.choices = [
            ("", "None"),
            ("p-4", "4"),
            ("w-full", "Full"),
            ("h-svw", "Smallest visible width"),
        ]
        html = widget.render("__NAME__", "p-4", attrs={"id": "__ID__"})
        assert "Preset sizes" in html
        assert "Responsive sizes" in html
        assert 'value="w-full"' in html
        assert 'value="h-svw"' in html


class TestDaisyUINumberSliderWidget:
    def _widget(self, **kwargs):
        options = {"min_value": 0, "max_value": 999, "step": 1, "suffix": "px"}
        options.update(kwargs)
        return DaisyUINumberSliderWidget(**options)

    def test_renders_range_and_number_inputs(self):
        html = self._widget().render("__NAME__", 12, attrs={"id": "__ID__"})
        assert 'name="__NAME__"' in html
        assert 'id="__ID__"' in html
        assert "daisyui-number-slider-widget" in html
        assert 'type="range"' in html
        assert 'type="number"' in html
        assert 'min="0"' in html
        assert 'max="999"' in html
        assert 'step="1"' in html
        assert 'value="12"' in html

    def test_suffix_is_shown_in_readout(self):
        html = self._widget(suffix="px").render("__NAME__", 8, attrs={"id": "__ID__"})
        assert "8px" in html
        assert 'data-suffix="px"' in html

    def test_none_value_renders_empty_number_input(self):
        html = self._widget().render("__NAME__", None, attrs={"id": "__ID__"})
        assert 'value=""' in html
        assert "None" in html

    def test_range_position_is_clamped_to_bounds(self):
        widget = DaisyUINumberSliderWidget(min_value=0, max_value=10, step=1)
        html = widget.render("__NAME__", 50, attrs={"id": "__ID__"})
        assert 'value="10"' in html

    def test_number_value_is_the_value_carrier(self):
        html = self._widget().render("__NAME__", 12, attrs={"id": "__ID__"})
        number_input = html.split('type="number"', 1)[1].split(">", 1)[0]
        assert 'name="__NAME__"' in number_input
        assert 'value="12"' in number_input


class TestDaisyUIAlignWidget:
    def test_renders_icons_for_choices(self):
        widget = DaisyUIAlignWidget()
        widget.choices = [
            ("", "None"),
            ("text-left", "Left"),
            ("text-center", "Center"),
            ("text-right", "Right"),
            ("text-justify", "Justify"),
        ]
        html = widget.render("__NAME__", "text-center", attrs={"id": "__ID__"})
        assert 'value="text-center"' in html
        assert "daisyui-align-widget" in html
        assert "daisyui-align-icon" in html


class TestBlockWidgets:
    def test_typography_design_uses_custom_widgets(self):
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
            widget = typography.child_blocks[name].field.widget
            assert isinstance(widget, widget_class), f"{name}: {type(widget)}"

    def test_typography_block_has_no_bg_image(self):
        typography = InlineTextBlock().child_blocks["design"].child_blocks["typography"]
        assert "bg_image" not in typography.child_blocks

    def test_container_block_has_bg_image(self):
        background = CardBlock().child_blocks["design"].child_blocks["background"]
        assert "bg_image" in background.child_blocks
        assert "bg_color" in background.child_blocks

    def test_button_block_has_button_appearance(self):
        design = ButtonBlock().child_blocks["design"]
        assert "button_appearance" in design.child_blocks

    def test_section_block_has_background(self):
        design = SectionBlock().child_blocks["design"]
        assert "background" in design.child_blocks

    def test_numeric_blocks_use_number_slider(self):
        from wagtail_daisIE.base_blocks.background_layer import (
            BackgroundLayerBlock,
            GradientStopBlock,
        )
        from wagtail_daisIE.blocks.layout import GridBlock

        mapping = [
            (BorderBlock(), "border_width"),
            (GridBlock(), "num_columns"),
            (GradientStopBlock(), "position"),
            (BackgroundLayerBlock(), "gradient_angle"),
        ]
        for block, field_name in mapping:
            child = block.child_blocks[field_name]
            assert isinstance(child, DaisyUIIntegerBlock), field_name
            assert isinstance(child.field.widget, DaisyUINumberSliderWidget), field_name


@pytest.mark.django_db
class TestNoImportTimeQueries:
    """Guards against Django's "database during app initialization" warning.

    Widgets are instantiated at import time inside block class bodies, so a
    query in ``__init__`` runs before the app registry is ready.
    """

    def test_swatch_widget_init_does_not_query(self):
        with CaptureQueriesContext(connection) as ctx:
            DaisyUISwatchWidget(prefix="bg")
            DaisyUIRawSwatchWidget(prefix="bg")
        assert len(ctx) == 0

    def test_blocks_import_does_not_query(self):
        for name in list(sys.modules):
            if name.startswith("wagtail_daisIE.base_blocks"):
                del sys.modules[name]
        with CaptureQueriesContext(connection) as ctx:
            importlib.import_module("wagtail_daisIE.base_blocks.background_layer")
            importlib.import_module("wagtail_daisIE.base_blocks.fields")
        assert len(ctx) == 0

    def test_widget_color_map_is_computed_lazily(self):
        widget = DaisyUISwatchWidget(prefix="bg")
        with CaptureQueriesContext(connection) as ctx:
            assert widget.color_map["bg-primary"] != "#cccccc"
        assert len(ctx) >= 1


class TestStyledPageMixinLazyTheme:
    def test_mixin_has_no_eager_init(self):
        assert "__init__" not in StyledPageMixin.__dict__

    @pytest.mark.django_db
    def test_default_theme_id_is_resolved_lazily(self):
        theme = DaisyUITheme.objects.create(name="lazy-default", default=True)
        assert get_default_theme_id() == theme.pk


class TestWidgetAdapters:
    def test_widgets_pack_with_expected_constructors(self):
        block = InlineTextBlock()
        context = JSContext()
        packed = context.pack(block)
        import json

        payload = json.dumps(packed)
        assert "wagtail_daisIE.widgets.SwatchSelect" in payload
        assert "wagtail_daisIE.widgets.SliderSelect" in payload
        assert "wagtail_daisIE.widgets.NumberSlider" in payload
        assert "wagtail_daisIE.widgets.AlignSelect" in payload
