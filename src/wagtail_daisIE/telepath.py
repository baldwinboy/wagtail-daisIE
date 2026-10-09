from wagtail.admin.telepath import Adapter, register

from wagtail_daisIE.widgets import (
    DaisyUINumberSliderWidget,
    DaisyUISliderWidget,
    DaisyUISwatchWidget,
)


class DaisyUISwatchWidgetAdapter(Adapter):
    js_constructor = "wagtail_daisIE.widgets.SwatchSelect"

    def js_args(self, widget):
        return [
            widget.render("__NAME__", None, attrs={"id": "__ID__"}),
        ]


register(DaisyUISwatchWidgetAdapter(), DaisyUISwatchWidget)


class DaisyUISliderWidgetAdapter(Adapter):
    js_constructor = "wagtail_daisIE.widgets.SliderSelect"

    def js_args(self, widget):
        return [
            widget.render("__NAME__", None, attrs={"id": "__ID__"}),
        ]


register(DaisyUISliderWidgetAdapter(), DaisyUISliderWidget)


class DaisyUINumberSliderWidgetAdapter(Adapter):
    js_constructor = "wagtail_daisIE.widgets.NumberSlider"

    def js_args(self, widget):
        return [
            widget.render("__NAME__", None, attrs={"id": "__ID__"}),
        ]


register(DaisyUINumberSliderWidgetAdapter(), DaisyUINumberSliderWidget)
