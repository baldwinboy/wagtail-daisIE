import importlib
import sys

import pytest

from django.db import connection
from django.test.utils import CaptureQueriesContext

from wagtail_daisIE.models import DaisyUITheme
from wagtail_daisIE.pages import get_default_theme_id
from wagtail_daisIE.widgets import (
    DaisieAutocompleteSelectMultiple,
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
        assert (
            'data-daisie-swatch-prefix-value="bg"' in html and 'value="#ff0000"' in html
        )
        assert 'data-controller="daisie-swatch"' in html
        assert "<details" in html and 'name="daisie-swatch-widget"' in html
        assert '<summary class="w-label-3">' in html
        assert 'data-daisie-swatch-target="radio"' in html
        assert 'data-daisie-swatch-target="input"' in html
        assert 'class="w-sr-only"' in html
        assert "daisyui-swatch-chip--custom" in html
        assert "swatch_controller.js" in str(widget.media)

        color_map = widget.color_map
        for name in ("primary", "secondary", "accent", "neutral", "info", "success"):
            # The content colour must be distinct from the base colour.
            assert f"bg-{name}-content" in color_map
            assert color_map[f"bg-{name}-content"] not in (
                "#cccccc",
                color_map[f"bg-{name}"],
            )


@pytest.mark.django_db
class TestSwatchTelepathAdapter:
    def test_adapter_registered_and_includes_media(self):
        from wagtail.admin.telepath import registry

        from wagtail_daisIE.telepath import DaisyUISwatchWidgetAdapter

        widget = DaisyUISwatchWidget(prefix="bg")
        adapter = DaisyUISwatchWidgetAdapter()
        assert "__NAME__" in adapter.js_args(widget)[0]
        assert "swatch_controller.js" in str(adapter.get_media(widget))
        assert isinstance(
            registry.find_adapter(DaisyUIRawSwatchWidget),
            DaisyUISwatchWidgetAdapter,
        )


class TestWidgetRendering:
    def test_raw_swatch(self):
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
        raw_html = raw.render("bg_color", "#1e0000", attrs={"id": "__ID__"})
        assert 'value="#1e0000"' in raw_html
        assert 'data-raw="true"' in raw_html
        assert 'data-daisie-swatch-prefix-value=""' in raw_html

    def test_preset_slider(self):
        slider = DaisyUISliderWidget()
        slider.choices = [("", "None"), ("m-auto", "Auto"), ("m-4", "4")]
        html = slider.render("__NAME__", "m-auto", attrs={"id": "__ID__"})
        assert 'data-controller="daisie-preset-slider"' in html
        assert 'data-daisie-preset-slider-target="range"' in html
        assert 'aria-valuetext="Auto"' in html
        assert 'data-daisie-preset-semantic="1"' in html

    def test_number_slider(self):
        number = DaisyUINumberSliderWidget(min_value=0, max_value=10, step=1)
        html = number.render("__NAME__", 5, attrs={"id": "__ID__"})
        assert 'data-controller="daisie-number-slider"' in html
        assert 'data-daisie-number-slider-target="range"' in html
        assert 'data-daisie-number-slider-target="number"' in html
        assert "daisyui-slider-value" not in html
        assert "number_slider_controller.js" in str(number.media)

    def test_autocomplete(self):
        autocomplete = DaisieAutocompleteSelectMultiple(
            choices=[("a", "Alpha"), ("b", "Bravo")], placeholder="Pick"
        )
        html = autocomplete.render("tags", ["a"], attrs={"id": "__ID__"})
        assert 'name="tags"' in html
        assert "data-daisyui-autocomplete" in html
        assert 'value="a" selected' in html
        assert "Alpha" in html and "Bravo" in html
        assert "daisyui_autocomplete.js" in str(autocomplete.media)


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
