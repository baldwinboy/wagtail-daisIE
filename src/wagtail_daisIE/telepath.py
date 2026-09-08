from wagtail.admin.telepath import Adapter, register

from wagtail_daisIE.widgets import (
    DaisyUIAlignWidget,
    DaisyUINumberSliderWidget,
    DaisyUISliderWidget,
    DaisyUISwatchWidget,
)

from .icons.widgets import IconChooserWidget


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


class DaisyUIAlignWidgetAdapter(Adapter):
    js_constructor = "wagtail_daisIE.widgets.AlignSelect"

    def js_args(self, widget):
        return [
            widget.render("__NAME__", None, attrs={"id": "__ID__"}),
        ]


register(DaisyUIAlignWidgetAdapter(), DaisyUIAlignWidget)


class IconChooserWidgetAdapter(Adapter):
    js_constructor = "wagtail_daisIE.widgets.IconChooser"

    def js_args(self, widget):
        return [
            widget.render("__NAME__", None, attrs={"id": "__ID__"}),
        ]


register(IconChooserWidgetAdapter(), IconChooserWidget)
